"""
Connected mailbox scanner (Gmail and Outlook through OAuth).

    connect  -> provider consent screen (read-only by default) -> callback
    callback -> exchange the code, store encrypted tokens, first sync
    sync     -> new inbox emails since the last cursor, as raw MIME (real headers:
                SPF/DKIM/DMARC, reply-to, attachments) -> analysis pipeline
             -> threats: stored for the user (notifications) + SOC correlation,
                optional "PhishGuard" label/category in the mailbox
    disconnect -> revoke at the provider, delete the tokens

Privacy: only the verdict, sender, subject and suspicious links are kept for
safe emails - never their body. Scheduling: app/services/scheduler.py.

Configuration (.env): GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET (Gmail API enabled),
MICROSOFT_CLIENT_ID / MICROSOFT_CLIENT_SECRET, MAILBOX_REDIRECT_BASE (defaults to
FRONTEND_URL, e.g. http://localhost:5173 - the Vite proxy forwards /api).
"""
from __future__ import annotations

import base64
import logging
import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests

from app import db
from app.models import Analysis, MailboxConnection
from app.services import crypto_box

log = logging.getLogger(__name__)

TIMEOUT = 15
INITIAL_DAYS = int(os.getenv('MAILBOX_INITIAL_DAYS', '14'))
MAX_PER_SYNC = int(os.getenv('MAILBOX_MAX_PER_SYNC', '25'))
MAX_RAW_BYTES = 5 * 1024 * 1024
LABEL_NAME = 'PhishGuard ⚠'


class MailboxError(Exception):
    """Provider problem shown to the user (code is a translation key suffix)."""

    def __init__(self, code: str, detail: str = ''):
        super().__init__(detail or code)
        self.code = code


def redirect_uri(provider: str) -> str:
    base = (os.getenv('MAILBOX_REDIRECT_BASE') or os.getenv('FRONTEND_URL') or 'http://localhost:5173').rstrip('/')
    return f'{base}/api/mailbox/callback/{provider}'


# ---------------------------------------------------------------- providers

class Gmail:
    name = 'gmail'
    AUTH = 'https://accounts.google.com/o/oauth2/v2/auth'
    TOKEN = 'https://oauth2.googleapis.com/token'
    API = 'https://gmail.googleapis.com/gmail/v1/users/me'
    READ = 'https://www.googleapis.com/auth/gmail.readonly'
    MODIFY = 'https://www.googleapis.com/auth/gmail.modify'

    @staticmethod
    def credentials():
        return os.getenv('GOOGLE_CLIENT_ID'), os.getenv('GOOGLE_CLIENT_SECRET')

    def auth_url(self, state: str, label: bool) -> str:
        client_id, _ = self.credentials()
        scopes = ['openid', 'email', self.MODIFY if label else self.READ]
        return self.AUTH + '?' + urlencode({
            'client_id': client_id, 'redirect_uri': redirect_uri(self.name), 'response_type': 'code',
            'scope': ' '.join(scopes), 'access_type': 'offline', 'prompt': 'consent',
            'include_granted_scopes': 'true', 'state': state,
        })

    def exchange(self, code: str) -> dict:
        client_id, secret = self.credentials()
        return _token_request(self.TOKEN, {'code': code, 'client_id': client_id, 'client_secret': secret,
                                           'redirect_uri': redirect_uri(self.name),
                                           'grant_type': 'authorization_code'})

    def refresh(self, refresh_token: str) -> dict:
        client_id, secret = self.credentials()
        return _token_request(self.TOKEN, {'refresh_token': refresh_token, 'client_id': client_id,
                                           'client_secret': secret, 'grant_type': 'refresh_token'})

    def account_email(self, token: str) -> str:
        return _get(f'{self.API}/profile', token).json()['emailAddress']

    def list_new(self, token: str, since: datetime) -> list[tuple[str, datetime]]:
        query = f'in:inbox after:{int(since.timestamp())}'
        data = _get(f'{self.API}/messages', token, params={'q': query, 'maxResults': MAX_PER_SYNC}).json()
        return [(m['id'], since) for m in data.get('messages', [])]

    def raw(self, token: str, message_id: str) -> tuple[bytes, datetime | None]:
        data = _get(f'{self.API}/messages/{message_id}', token, params={'format': 'raw'}).json()
        received = datetime.utcfromtimestamp(int(data.get('internalDate', '0')) / 1000) if data.get('internalDate') else None
        return base64.urlsafe_b64decode(data['raw'] + '=' * (-len(data['raw']) % 4)), received

    def label(self, token: str, message_id: str) -> None:
        labels = _get(f'{self.API}/labels', token).json().get('labels', [])
        label_id = next((lb['id'] for lb in labels if lb['name'] == LABEL_NAME), None)
        if label_id is None:
            label_id = _send('post', f'{self.API}/labels', token,
                             json={'name': LABEL_NAME, 'labelListVisibility': 'labelShow',
                                   'messageListVisibility': 'show'}).json()['id']
        _send('post', f'{self.API}/messages/{message_id}/modify', token, json={'addLabelIds': [label_id]})

    def revoke(self, token: str) -> None:
        requests.post('https://oauth2.googleapis.com/revoke', params={'token': token}, timeout=TIMEOUT)


class Outlook:
    name = 'outlook'
    BASE = 'https://login.microsoftonline.com/common/oauth2/v2.0'
    API = 'https://graph.microsoft.com/v1.0/me'

    @staticmethod
    def credentials():
        return os.getenv('MICROSOFT_CLIENT_ID'), os.getenv('MICROSOFT_CLIENT_SECRET')

    @staticmethod
    def scopes(label: bool) -> str:
        return ' '.join(['openid', 'email', 'offline_access', 'User.Read', 'Mail.ReadWrite' if label else 'Mail.Read'])

    def auth_url(self, state: str, label: bool) -> str:
        client_id, _ = self.credentials()
        return f'{self.BASE}/authorize?' + urlencode({
            'client_id': client_id, 'redirect_uri': redirect_uri(self.name), 'response_type': 'code',
            'response_mode': 'query', 'scope': self.scopes(label), 'state': state, 'prompt': 'select_account',
        })

    def exchange(self, code: str) -> dict:
        client_id, secret = self.credentials()
        return _token_request(f'{self.BASE}/token', {'code': code, 'client_id': client_id, 'client_secret': secret,
                                                     'redirect_uri': redirect_uri(self.name),
                                                     'grant_type': 'authorization_code'})

    def refresh(self, refresh_token: str) -> dict:
        client_id, secret = self.credentials()
        return _token_request(f'{self.BASE}/token', {'refresh_token': refresh_token, 'client_id': client_id,
                                                     'client_secret': secret, 'grant_type': 'refresh_token'})

    def account_email(self, token: str) -> str:
        me = _get(self.API, token, params={'$select': 'mail,userPrincipalName'}).json()
        return me.get('mail') or me['userPrincipalName']

    def list_new(self, token: str, since: datetime) -> list[tuple[str, datetime]]:
        data = _get(f'{self.API}/mailFolders/inbox/messages', token, params={
            '$select': 'id,receivedDateTime', '$top': MAX_PER_SYNC, '$orderby': 'receivedDateTime desc',
            '$filter': f"receivedDateTime gt {since.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        }).json()
        return [(m['id'], _parse_iso(m['receivedDateTime'])) for m in data.get('value', [])]

    def raw(self, token: str, message_id: str) -> tuple[bytes, datetime | None]:
        return _get(f'{self.API}/messages/{message_id}/$value', token).content, None

    def label(self, token: str, message_id: str) -> None:
        _send('patch', f'{self.API}/messages/{message_id}', token, json={'categories': [LABEL_NAME]})

    def revoke(self, token: str) -> None:
        # Personal Microsoft accounts have no token revocation endpoint: tokens are
        # deleted locally and the user can remove the app at account.live.com/consent
        return None


PROVIDERS = {'gmail': Gmail(), 'outlook': Outlook()}


def configured() -> dict[str, bool]:
    return {name: all(p.credentials()) for name, p in PROVIDERS.items()}


# ---------------------------------------------------------------- HTTP helpers

def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)


def _token_request(url: str, data: dict) -> dict:
    try:
        response = requests.post(url, data=data, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise MailboxError('unreachable', str(exc)) from exc
    if response.status_code >= 400:
        body = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
        code = 'revoked' if body.get('error') == 'invalid_grant' else 'token'
        raise MailboxError(code, body.get('error_description') or response.text[:200])
    return response.json()


def _send(method: str, url: str, token: str, **kw):
    try:
        response = requests.request(method, url, headers={'Authorization': f'Bearer {token}'}, timeout=TIMEOUT, **kw)
    except requests.RequestException as exc:
        raise MailboxError('unreachable', str(exc)) from exc
    if response.status_code == 401:
        raise MailboxError('unauthorized', response.text[:200])
    if response.status_code == 403:
        raise MailboxError('forbidden', response.text[:200])
    if response.status_code >= 400:
        raise MailboxError('provider', f'{response.status_code} {response.text[:200]}')
    return response


def _get(url: str, token: str, **kw):
    return _send('get', url, token, **kw)


# ---------------------------------------------------------------- connection lifecycle

def new_state() -> str:
    return secrets.token_urlsafe(24)


def _store_tokens(conn: MailboxConnection, tokens: dict) -> None:
    conn.access_token_enc = crypto_box.encrypt(tokens['access_token'])
    if tokens.get('refresh_token'):
        conn.refresh_token_enc = crypto_box.encrypt(tokens['refresh_token'])
    conn.token_expires_at = datetime.utcnow() + timedelta(seconds=int(tokens.get('expires_in', 3600)) - 60)
    if tokens.get('scope'):
        conn.scopes = tokens['scope']


def complete_connection(user_id: int, provider: str, code: str, label: bool) -> MailboxConnection:
    impl = PROVIDERS[provider]
    tokens = impl.exchange(code)
    email = impl.account_email(tokens['access_token']).lower()
    conn = MailboxConnection.query.filter_by(user_id=user_id, provider=provider, email=email).first()
    if conn is None:
        conn = MailboxConnection(user_id=user_id, provider=provider, email=email)
        db.session.add(conn)
    _store_tokens(conn, tokens)
    conn.status, conn.last_error, conn.auto_label = 'active', None, label
    conn.sync_cursor = conn.sync_cursor or (datetime.utcnow() - timedelta(days=INITIAL_DAYS)).isoformat()
    db.session.commit()
    return conn


def access_token(conn: MailboxConnection) -> str:
    """Valid access token, refreshed when expired.

    Tokens encrypted with another MAILBOX_ENCRYPTION_KEY (key changed or set after
    connecting) cannot be read: the user simply has to reconnect the mailbox.
    """
    try:
        return _access_token(conn)
    except crypto_box.DecryptionError as exc:
        raise MailboxError('revoked', 'stored token unreadable (encryption key changed)') from exc


def _access_token(conn: MailboxConnection) -> str:
    if conn.token_expires_at and conn.token_expires_at > datetime.utcnow():
        return crypto_box.decrypt(conn.access_token_enc)
    refresh_token = crypto_box.decrypt(conn.refresh_token_enc)
    if not refresh_token:
        raise MailboxError('revoked', 'no refresh token')
    _store_tokens(conn, PROVIDERS[conn.provider].refresh(refresh_token))
    db.session.commit()
    return crypto_box.decrypt(conn.access_token_enc)


def disconnect(conn: MailboxConnection) -> None:
    try:
        token = crypto_box.decrypt(conn.refresh_token_enc) or crypto_box.decrypt(conn.access_token_enc)
        if token:
            PROVIDERS[conn.provider].revoke(token)
    except Exception:  # revocation is best effort; local tokens are deleted anyway
        log.warning('Token revocation failed for mailbox %s', conn.id)
    db.session.delete(conn)
    db.session.commit()


# ---------------------------------------------------------------- live progress

# Per-mailbox progress of the scan in progress (or the last one, kept a few minutes),
# read by GET /api/mailbox/<id>/progress to animate the scan in the dashboard.
# In memory: fine for one server process; with several workers it would move to Redis.
_progress: dict[int, dict] = {}
FEED_SIZE = 12


def progress(conn_id: int) -> dict:
    state = _progress.get(conn_id)
    if not state:
        return {'state': 'idle'}
    if state['state'] != 'running' and state.get('finished_ts', 0) < datetime.utcnow().timestamp() - 300:
        _progress.pop(conn_id, None)
        return {'state': 'idle'}
    return {k: v for k, v in state.items() if k != 'finished_ts'}


def is_running(conn_id: int) -> bool:
    return _progress.get(conn_id, {}).get('state') == 'running'


def _start_progress(conn_id: int) -> dict:
    state = {'state': 'running', 'phase': 'listing', 'total': 0, 'done': 0, 'threats': 0, 'current': None,
             'feed': [], 'started_at': datetime.utcnow().isoformat() + 'Z'}
    _progress[conn_id] = state
    return state


def _finish_progress(state: dict, outcome: str, error: str | None = None) -> None:
    state.update(state=outcome, phase=outcome, current=None, error=error,
                 finished_at=datetime.utcnow().isoformat() + 'Z', finished_ts=datetime.utcnow().timestamp())


def _headers(raw: bytes) -> dict:
    """Subject and sender of an email, to show which email is being analysed."""
    from email import policy
    from email.parser import BytesHeaderParser
    try:
        msg = BytesHeaderParser(policy=policy.default).parsebytes(raw)
        return {'subject': str(msg.get('Subject') or '')[:140], 'sender': str(msg.get('From') or '')[:140]}
    except Exception:
        return {'subject': '', 'sender': ''}


# ---------------------------------------------------------------- sync

def sync(conn: MailboxConnection, lang: str = 'fr') -> dict:
    """Scan new inbox emails. Returns {'scanned', 'threats'}; never raises for one bad email."""
    state = _start_progress(conn.id)
    try:
        result = _sync(conn, lang, state)
    except MailboxError as exc:
        _finish_progress(state, 'error', exc.code)
        raise
    except Exception:
        _finish_progress(state, 'error', 'provider')
        raise
    _finish_progress(state, 'done')
    return result


def _sync(conn: MailboxConnection, lang: str, state: dict) -> dict:
    from app.pipeline import ParseError, run_pipeline
    from app.services import scan_service

    impl = PROVIDERS[conn.provider]
    try:
        token = access_token(conn)
        since = datetime.fromisoformat(conn.sync_cursor) if conn.sync_cursor else \
            datetime.utcnow() - timedelta(days=INITIAL_DAYS)
        messages = impl.list_new(token, since)
    except MailboxError as exc:
        conn.status = 'revoked' if exc.code in ('revoked', 'unauthorized') else 'error'
        conn.last_error = exc.code
        db.session.commit()
        raise

    scanned = threats = 0
    newest = since
    started = datetime.utcnow()
    todo = [(mid, rec) for mid, rec in messages
            if not Analysis.query.filter_by(mailbox_id=conn.id, external_id=mid).first()]
    state.update(phase='scanning', total=len(todo))
    for message_id, received in todo:
        state['current'] = {'subject': '', 'sender': '', 'step': 'download'}
        try:
            raw, received_at = impl.raw(token, message_id)
            if len(raw) > MAX_RAW_BYTES:
                state['done'] += 1
                continue
            state['current'] = {**_headers(raw), 'step': 'analyse'}
            result = run_pipeline(raw_eml=raw, source='mailbox', lang=lang)
        except (ParseError, MailboxError, Exception) as exc:
            if not isinstance(exc, (ParseError, MailboxError)):
                log.exception('Mailbox %s: message %s could not be analysed', conn.id, message_id)
            else:
                log.warning('Mailbox %s: message %s skipped (%s)', conn.id, message_id, type(exc).__name__)
            state['done'] += 1
            continue
        scan_service.finalize(result)
        dangerous = result['verdict'] in ('phishing', 'suspicious')
        analysis = scan_service.save(result, user_id=conn.user_id, source='mailbox', text=_body_preview(raw),
                                     mailbox_id=conn.id, external_id=message_id, keep_body=dangerous)
        scanned += 1
        threats += dangerous
        state['done'] += 1
        state['threats'] = threats
        state['feed'] = [{'analysis_id': analysis.id, 'subject': state['current'].get('subject') or '',
                          'sender': state['current'].get('sender') or '', 'verdict': result['verdict'],
                          'score': round(result['score']), 'brand': result.get('brand')}] + state['feed'][:FEED_SIZE - 1]
        newest = max(newest, received_at or received)
        if dangerous and conn.auto_label:
            try:
                impl.label(token, message_id)
            except MailboxError:
                log.info('Mailbox %s: could not label message (scope?)', conn.id)

    # Gmail's after: filter has 1 s resolution; the unique index prevents duplicates
    conn.sync_cursor = (newest if messages else max(since, started - timedelta(minutes=5))).isoformat()
    conn.scanned_count += scanned
    conn.threat_count += threats
    conn.last_sync_at = datetime.utcnow()
    conn.status, conn.last_error = 'active', None
    db.session.commit()
    if threats:
        from app.services import audit_service
        audit_service.record('mailbox.threats', user_id=conn.user_id, actor_id=conn.user_id,
                             details={'mailbox': conn.email, 'provider': conn.provider, 'threats': threats},
                             severity='warning')
    return {'scanned': scanned, 'threats': threats}


def _body_preview(raw: bytes) -> str:
    """Readable text of an email (for the history of *dangerous* emails only)."""
    from app.pipeline.parser import parse_eml
    try:
        return parse_eml(raw).text[:1000]
    except Exception:
        return ''


def sync_all_due(interval_minutes: int) -> int:
    """Called by the scheduler: sync every active mailbox not synced for `interval_minutes`."""
    due = datetime.utcnow() - timedelta(minutes=interval_minutes)
    conns = MailboxConnection.query.filter(
        MailboxConnection.status.in_(('active', 'error')),
        db.or_(MailboxConnection.last_sync_at.is_(None), MailboxConnection.last_sync_at < due)).all()
    done = 0
    for conn in conns:
        try:
            sync(conn)
            done += 1
        except MailboxError:
            continue
        except Exception:
            log.exception('Mailbox %s sync failed', conn.id)
            db.session.rollback()
    return done
