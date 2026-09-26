"""
Admin security centre (/api/admin/security).

    GET  /overview          security posture of the signed-in admin (score + checks),
                            recent logins, platform alert counters
    POST /sudo              re-authenticate (password + TOTP) for sensitive actions
    POST /sign-out-others   end every other session of this account
    GET  /events            audit log (all security events, filterable, paginated)
    GET  /events/export     the same as CSV (evidence for an investigation)
    GET  /alerts            latest warning / critical events for the alert feed
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta

import bcrypt
import pyotp
from flask import Blueprint, Response, request
from flask_login import current_user, login_user
from sqlalchemy import or_

from app import db
from app.api.admin import admin_required
from app.api.responses import err, ok
from app.api.security import grant_sudo, sudo_active
from app.models import SecurityEvent, User
from app.services import audit_service, settings_service

admin_security_bp = Blueprint('admin_security', __name__)

AUTH_EVENTS = ('login_success', 'login_failed', 'login_blocked', 'account_locked', 'mfa_failed',
               'mfa_enabled', 'mfa_disabled', 'password_changed', 'logout', 'sudo_granted', 'sudo_failed',
               'sessions_revoked')


def _names(events) -> dict[int, str]:
    ids = {e.user_id for e in events if e.user_id} | {e.actor_id for e in events if e.actor_id}
    return {u.id: u.email for u in User.query.filter(User.id.in_(ids)).all()} if ids else {}


def _posture(user: User) -> dict:
    """Security score of an admin account from concrete, fixable checks."""
    now = datetime.utcnow()
    failures = audit_service.recent_failures(user.id, minutes=7 * 24 * 60)
    password_age = (now - user.password_changed_at).days if user.password_changed_at else None
    new_locations = SecurityEvent.query.filter(
        SecurityEvent.user_id == user.id, SecurityEvent.event_type == 'login_success',
        SecurityEvent.created_at >= now - timedelta(days=30), SecurityEvent.severity == 'warning').count()
    checks = [
        {'key': 'mfa', 'ok': bool(user.mfa_active), 'weight': 35},
        {'key': 'password_age', 'ok': password_age is not None and password_age <= 90, 'weight': 15,
         'value': password_age},
        {'key': 'email_verified', 'ok': bool(user.email_verified), 'weight': 10},
        {'key': 'no_failed_logins', 'ok': failures == 0, 'weight': 15, 'value': failures},
        {'key': 'no_new_locations', 'ok': new_locations == 0, 'weight': 10, 'value': new_locations},
        {'key': 'platform_mfa', 'ok': bool(settings_service.get('mfa_required')), 'weight': 10},
        {'key': 'profile_complete', 'ok': bool(user.full_name and user.phone_number), 'weight': 5},
    ]
    score = sum(c['weight'] for c in checks if c['ok'])
    return {'score': score, 'grade': 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 50 else 'D',
            'checks': checks}


@admin_security_bp.route('/overview', methods=['GET'])
@admin_required
def overview():
    from app.api.user_profile import _serialize
    day_ago = datetime.utcnow() - timedelta(hours=24)
    logins = (SecurityEvent.query.filter(SecurityEvent.user_id == current_user.id,
                                         SecurityEvent.event_type.in_(('login_success', 'login_failed', 'mfa_failed',
                                                                       'login_blocked', 'account_locked')))
              .order_by(SecurityEvent.created_at.desc()).limit(12).all())
    from flask import session  # sudo expiry lives in the signed session cookie
    return ok({
        'profile': {**_serialize(current_user), 'job_title': current_user.job_title,
                    'organization': current_user.organization, 'city': current_user.city},
        'posture': _posture(current_user),
        'logins': [audit_service.serialize(e, {current_user.id: current_user.email}) for e in logins],
        'sudo': {'active': sudo_active(), 'until': session.get('sudo_until'),
                 'minutes': settings_service.get('sudo_minutes')},
        'platform': {
            'failed_logins_24h': SecurityEvent.query.filter(SecurityEvent.event_type.in_(('login_failed', 'mfa_failed')),
                                                            SecurityEvent.created_at >= day_ago).count(),
            'locked_accounts': User.query.filter(User.locked_until > datetime.utcnow()).count(),
            'admins': User.query.filter_by(is_admin=True).count(),
            'admins_without_mfa': User.query.filter_by(is_admin=True, mfa_active=False).count(),
            'pending_accounts': User.query.filter(User.approval_status.in_(('pending', 'review'))).count(),
            'warnings_24h': SecurityEvent.query.filter(SecurityEvent.severity != 'info',
                                                       SecurityEvent.created_at >= day_ago).count(),
        },
    })


@admin_security_bp.route('/sudo', methods=['POST'])
@admin_required
def sudo():
    data = request.get_json(silent=True) or {}
    password = (data.get('password') or '').encode('utf-8')
    valid = bool(password) and bcrypt.checkpw(password, current_user.password_hash.encode('utf-8'))
    if valid and current_user.mfa_active and current_user.mfa_secret:
        valid = pyotp.TOTP(current_user.mfa_secret).verify(str(data.get('code') or ''))
    if not valid:
        audit_service.record('sudo_failed', user_id=current_user.id)
        return err('SUDO_FAILED', 'Mot de passe ou code incorrect.', 403)
    until = grant_sudo(settings_service.get('sudo_minutes') or 10)
    audit_service.record('sudo_granted', user_id=current_user.id)
    return ok({'active': True, 'until': until.isoformat(), 'mfa_required': bool(current_user.mfa_active)})


@admin_security_bp.route('/sign-out-others', methods=['POST'])
@admin_required
def sign_out_others():
    current_user.session_version = (current_user.session_version or 1) + 1
    db.session.commit()
    login_user(current_user)  # re-issue this session with the new version
    audit_service.record('sessions_revoked', user_id=current_user.id, severity='warning')
    return ok({'ok': True})


def _events_query():
    query = SecurityEvent.query
    scope = request.args.get('scope', 'all')
    if scope == 'auth':
        query = query.filter(SecurityEvent.event_type.in_(AUTH_EVENTS))
    elif scope == 'admin':
        query = query.filter(SecurityEvent.event_type.like('admin_%'))
    elif scope == 'registration':
        query = query.filter(SecurityEvent.event_type.like('registration%'))
    if request.args.get('severity') in ('info', 'warning', 'critical'):
        query = query.filter(SecurityEvent.severity == request.args['severity'])
    if request.args.get('type'):
        query = query.filter(SecurityEvent.event_type == request.args['type'])
    q = (request.args.get('q') or '').strip()
    if q:
        user_ids = [u.id for u in User.query.filter(User.email.ilike(f'%{q}%')).all()]
        query = query.filter(or_(SecurityEvent.ip.ilike(f'%{q}%'), SecurityEvent.event_type.ilike(f'%{q}%'),
                                 SecurityEvent.user_id.in_(user_ids), SecurityEvent.actor_id.in_(user_ids)))
    days = request.args.get('days', type=int)
    if days:
        query = query.filter(SecurityEvent.created_at >= datetime.utcnow() - timedelta(days=days))
    return query


@admin_security_bp.route('/events', methods=['GET'])
@admin_required
def events():
    page = max(1, request.args.get('page', default=1, type=int))
    per_page = min(100, max(1, request.args.get('per_page', default=25, type=int)))
    query = _events_query()
    total = query.count()
    rows = query.order_by(SecurityEvent.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    names = _names(rows)
    day_ago = datetime.utcnow() - timedelta(hours=24)
    return ok({
        'items': [audit_service.serialize(e, names) for e in rows], 'total': total, 'page': page, 'per_page': per_page,
        'counters': {
            'total_24h': SecurityEvent.query.filter(SecurityEvent.created_at >= day_ago).count(),
            'warning_24h': SecurityEvent.query.filter(SecurityEvent.severity == 'warning', SecurityEvent.created_at >= day_ago).count(),
            'critical_24h': SecurityEvent.query.filter(SecurityEvent.severity == 'critical', SecurityEvent.created_at >= day_ago).count(),
            'admin_actions_24h': SecurityEvent.query.filter(SecurityEvent.event_type.like('admin_%'), SecurityEvent.created_at >= day_ago).count(),
        },
    })


@admin_security_bp.route('/events/export', methods=['GET'])
@admin_required
def export_events():
    rows = _events_query().order_by(SecurityEvent.created_at.desc()).limit(10000).all()
    names = _names(rows)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['created_at', 'event', 'severity', 'user', 'actor', 'ip', 'location', 'device', 'details'])
    for e in rows:
        item = audit_service.serialize(e, names)
        writer.writerow([item['created_at'], item['type'], item['severity'], item['user'] or '', item['actor'] or '',
                         item['ip'] or '', item['location'] or '', item['device'], item['details']])
    audit_service.record('admin_audit_exported', details={'rows': len(rows)})
    return Response(buffer.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=phishguard_audit.csv'})


@admin_security_bp.route('/alerts', methods=['GET'])
@admin_required
def alerts():
    rows = (SecurityEvent.query.filter(SecurityEvent.severity != 'info',
                                       SecurityEvent.created_at >= datetime.utcnow() - timedelta(days=7))
            .order_by(SecurityEvent.created_at.desc()).limit(15).all())
    names = _names(rows)
    return ok({'items': [audit_service.serialize(e, names) for e in rows]})
