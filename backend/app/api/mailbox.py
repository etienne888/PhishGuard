"""Connected mailboxes (Gmail / Outlook) and the forwarding address - /api/mailbox."""
from __future__ import annotations

import os
import threading

from flask import Blueprint, current_app, redirect, request, session
from flask_login import current_user, login_required

from app import db
from app.api.responses import err, ok
from app.models import MailboxConnection
from app.pipeline.i18n import request_lang, tr
from app.services import audit_service, inbound_service, mailbox_service
from app.services.mailbox_service import MailboxError

mailbox_bp = Blueprint('mailbox', __name__)


def _serialize(conn: MailboxConnection) -> dict:
    return {
        'id': conn.id, 'provider': conn.provider, 'email': conn.email, 'status': conn.status,
        'auto_label': conn.auto_label, 'scanned_count': conn.scanned_count, 'threat_count': conn.threat_count,
        'last_sync_at': conn.last_sync_at.isoformat() if conn.last_sync_at else None,
        'last_error': conn.last_error,
        'read_only': not conn.auto_label,
        'progress': mailbox_service.progress(conn.id),
        'created_at': conn.created_at.isoformat() if conn.created_at else None,
    }


def _own(conn_id: int) -> MailboxConnection | None:
    return MailboxConnection.query.filter_by(id=conn_id, user_id=current_user.id).first()


def _frontend(path: str) -> str:
    return (os.getenv('FRONTEND_URL') or 'http://localhost:5173').rstrip('/') + path


@mailbox_bp.route('', methods=['GET'])
@login_required
def list_mailboxes():
    rows = MailboxConnection.query.filter_by(user_id=current_user.id).order_by(MailboxConnection.created_at).all()
    return ok({
        'items': [_serialize(r) for r in rows],
        'providers': mailbox_service.configured(),
        'forward_address': inbound_service.address(),
    })


@mailbox_bp.route('/connect/<provider>', methods=['POST'])
@login_required
def connect(provider: str):
    if provider not in mailbox_service.PROVIDERS:
        return err('NOT_FOUND', 'Unknown provider', 404)
    if not mailbox_service.configured()[provider]:
        return err('NOT_CONFIGURED', tr(request_lang(), 'mailbox.not_configured'), 503)
    label = bool((request.get_json(silent=True) or {}).get('label'))
    state = mailbox_service.new_state()
    session['mailbox_oauth'] = {'state': state, 'provider': provider, 'label': label}
    return ok({'url': mailbox_service.PROVIDERS[provider].auth_url(state, label)})


def _first_sync(app, conn_id: int, lang: str):
    with app.app_context():
        conn = db.session.get(MailboxConnection, conn_id)
        try:
            if conn:
                mailbox_service.sync(conn, lang)
        except Exception:
            app.logger.exception('First mailbox sync failed')
            db.session.rollback()
        finally:
            db.session.remove()


@mailbox_bp.route('/callback/<provider>', methods=['GET'])
@login_required
def callback(provider: str):
    """The provider redirects the browser here after the consent screen."""
    pending = session.pop('mailbox_oauth', None) or {}
    if request.args.get('error'):
        return redirect(_frontend('/dashboard/mailboxes?error=denied'))
    if pending.get('provider') != provider or not pending.get('state') or \
            request.args.get('state') != pending['state']:
        return redirect(_frontend('/dashboard/mailboxes?error=state'))
    try:
        conn = mailbox_service.complete_connection(current_user.id, provider, request.args.get('code', ''),
                                                   bool(pending.get('label')))
    except MailboxError as exc:
        return redirect(_frontend(f'/dashboard/mailboxes?error={exc.code}'))
    except (KeyError, ValueError):
        return redirect(_frontend('/dashboard/mailboxes?error=provider'))
    audit_service.record('mailbox.connected', user_id=current_user.id,
                         details={'provider': provider, 'mailbox': conn.email, 'read_only': not conn.auto_label})
    # The first scan (last days of the inbox) can take a minute: run it in the background
    threading.Thread(target=_first_sync, args=(current_app._get_current_object(), conn.id, request_lang()),
                     daemon=True).start()
    return redirect(_frontend(f'/dashboard/mailboxes?connected={provider}'))


@mailbox_bp.route('/<int:conn_id>/sync', methods=['POST'])
@login_required
def sync_now(conn_id: int):
    """Start a scan in the background; the page follows it with GET /<id>/progress."""
    conn = _own(conn_id)
    if conn is None:
        return err('NOT_FOUND', tr(request_lang(), 'error.not_found'), 404)
    if conn.status == 'paused':
        return err('PAUSED', tr(request_lang(), 'mailbox.paused'), 409)
    if not mailbox_service.is_running(conn.id):
        mailbox_service._start_progress(conn.id)  # visible at once, and blocks a double start
        threading.Thread(target=_first_sync, args=(current_app._get_current_object(), conn.id, request_lang()),
                         daemon=True).start()
    return ok({'started': True, 'progress': mailbox_service.progress(conn.id)}, status=202)


@mailbox_bp.route('/<int:conn_id>/progress', methods=['GET'])
@login_required
def sync_progress(conn_id: int):
    """Live state of the scan: which email is being analysed, counters and the latest results."""
    conn = _own(conn_id)
    if conn is None:
        return err('NOT_FOUND', tr(request_lang(), 'error.not_found'), 404)
    return ok({**mailbox_service.progress(conn.id), 'mailbox': _serialize(conn)})


@mailbox_bp.route('/<int:conn_id>', methods=['PATCH'])
@login_required
def update(conn_id: int):
    conn = _own(conn_id)
    if conn is None:
        return err('NOT_FOUND', tr(request_lang(), 'error.not_found'), 404)
    body = request.get_json(silent=True) or {}
    if body.get('status') in ('active', 'paused'):
        conn.status = body['status']
    db.session.commit()
    return ok(_serialize(conn))


@mailbox_bp.route('/<int:conn_id>', methods=['DELETE'])
@login_required
def delete(conn_id: int):
    conn = _own(conn_id)
    if conn is None:
        return err('NOT_FOUND', tr(request_lang(), 'error.not_found'), 404)
    email, provider = conn.email, conn.provider
    mailbox_service.disconnect(conn)
    audit_service.record('mailbox.disconnected', user_id=current_user.id,
                         details={'provider': provider, 'mailbox': email})
    return ok({'deleted': True})
