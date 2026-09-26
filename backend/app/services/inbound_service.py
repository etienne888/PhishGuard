"""
"Forward it to PhishGuard": users forward a suspicious email to the PhishGuard
address and get the verdict back by email. Works with any mail provider and
needs no access to the user's mailbox.

The PhishGuard inbox is polled over IMAP (INBOUND_IMAP_HOST / INBOUND_IMAP_USER /
INBOUND_IMAP_PASSWORD, INBOUND_ADDRESS shown to users). Best results when the
email is forwarded *as an attachment* (.eml): the original headers
(SPF/DKIM/DMARC, reply-to) are kept. An inline forward is analysed as text.

- Registered, approved sender: the analysis is saved to their account and the
  verdict is emailed back.
- Unknown sender: analysed, but (like on the website) the reply only contains a
  "sign in to see the result" link with a claim token.
Loop protection: auto-generated emails and our own address are ignored; at most
MAX_PER_SENDER_DAY replies per sender per day.
"""
from __future__ import annotations

import base64
import email
import imaplib
import logging
import os
import quopri
from collections import defaultdict
from datetime import date
from email import policy
from email.utils import parseaddr

from app.models import User

log = logging.getLogger(__name__)

MAX_PER_SENDER_DAY = 20
MAX_BYTES = 5 * 1024 * 1024
_sent_today: dict[tuple[str, date], int] = defaultdict(int)


def configured() -> bool:
    return all(os.getenv(k) for k in ('INBOUND_IMAP_HOST', 'INBOUND_IMAP_USER', 'INBOUND_IMAP_PASSWORD'))


def address() -> str | None:
    if not configured():
        return None
    return os.getenv('INBOUND_ADDRESS') or os.getenv('INBOUND_IMAP_USER')


def _frontend() -> str:
    return (os.getenv('FRONTEND_URL') or 'http://localhost:5173').rstrip('/')


def _inner_message(outer: email.message.EmailMessage) -> tuple[bytes | None, str]:
    """The forwarded email: an attached message/rfc822 or .eml, else the forward's own text."""
    for part in outer.walk():
        if part.get_content_type() == 'message/rfc822':
            payload = part.get_payload()
            inner = payload[0] if isinstance(payload, list) and payload else payload
            raw = inner.as_bytes() if hasattr(inner, 'as_bytes') else str(inner).encode()
            # Some clients (and Python's add_attachment) base64/QP-encode the attached email
            encoding = (part.get('Content-Transfer-Encoding') or '').strip().lower()
            if encoding == 'base64':
                raw = base64.b64decode(b''.join(raw.split()))
            elif encoding == 'quoted-printable':
                raw = quopri.decodestring(raw)
            return raw, ''
        filename = (part.get_filename() or '').lower()
        if filename.endswith('.eml'):
            return part.get_payload(decode=True), ''
    body = outer.get_body(preferencelist=('plain', 'html'))
    text = body.get_content() if body else ''
    return None, text


def process(raw: bytes) -> str:
    """Analyse one received email and reply. Returns what happened (for logs/tests)."""
    from app.pipeline import ParseError, run_pipeline
    from app.pipeline.i18n import tr
    from app.services import mailer, scan_service
    from app.services.email_templates import verdict_email

    outer = email.message_from_bytes(raw, policy=policy.default)
    _, sender = parseaddr(outer.get('From', ''))
    sender = sender.lower()
    own = (address() or '').lower()
    if not sender or sender == own or (outer.get('Auto-Submitted', 'no').lower() != 'no') \
            or outer.get('Precedence', '').lower() in ('bulk', 'junk', 'list'):
        return 'ignored'
    key = (sender, date.today())
    if _sent_today[key] >= MAX_PER_SENDER_DAY:
        return 'rate_limited'

    inner_raw, text = _inner_message(outer)
    try:
        if inner_raw:
            result = run_pipeline(raw_eml=inner_raw[:MAX_BYTES], source='forward', lang='fr')
        else:
            result = run_pipeline(text=text[:20000], source='forward', lang='fr')
    except ParseError:
        return 'unreadable'
    scan_service.finalize(result)

    user = User.query.filter(User.email.ilike(sender)).first()
    known = user is not None and user.status != 'suspended' and (user.approval_status or 'approved') == 'approved'
    analysis = scan_service.save(result, user_id=user.id if known else None, source='forward',
                                 text=text if not inner_raw else '')
    checked = (result.get('message') or {}).get('subject') or outer.get('Subject', '')
    name = (user.full_name if known and user.full_name else sender.split('@')[0])
    if known:
        link = f'{_frontend()}/check?analysis={analysis.id}'
        reasons = [e for e, positive in zip(result.get('evidence', []), result.get('evidence_positive', []))
                   if not positive]
        subject, body, html = verdict_email(name, checked, result['verdict'], result['score'], reasons,
                                            result.get('recommendation') or tr('fr', 'default_recommendation'), link)
    else:
        token = scan_service.issue_claim(analysis)
        subject, body, html = verdict_email(name, checked, None, None, [], None,
                                            f'{_frontend()}/check?claim={token}')
    mailer.send(sender, subject, body, html, in_reply_to=outer.get('Message-ID'))
    _sent_today[key] += 1
    return 'replied' if known else 'invited'


def poll() -> int:
    """Fetch unread emails from the PhishGuard inbox and process them."""
    if not configured():
        return 0
    handled = 0
    host = os.getenv('INBOUND_IMAP_HOST')
    try:
        with imaplib.IMAP4_SSL(host, int(os.getenv('INBOUND_IMAP_PORT', '993'))) as imap:
            imap.login(os.getenv('INBOUND_IMAP_USER'), os.getenv('INBOUND_IMAP_PASSWORD'))
            imap.select('INBOX')
            _, ids = imap.search(None, 'UNSEEN')
            for msg_id in (ids[0].split() if ids and ids[0] else [])[:25]:
                _, data = imap.fetch(msg_id, '(RFC822)')
                raw = data[0][1] if data and isinstance(data[0], tuple) else None
                imap.store(msg_id, '+FLAGS', '\\Seen')
                if not raw or len(raw) > MAX_BYTES * 2:
                    continue
                try:
                    log.info('Inbound email %s: %s', msg_id.decode(), process(raw))
                    handled += 1
                except Exception:
                    log.exception('Inbound email %s failed', msg_id)
    except (imaplib.IMAP4.error, OSError):
        log.exception('Inbound mailbox polling failed')
    return handled
