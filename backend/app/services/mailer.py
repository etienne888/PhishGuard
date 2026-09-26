"""Send a branded HTML email through the configured SMTP account (logs when unset)."""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from pathlib import Path

from app.services.email_templates import LOGO_CID

log = logging.getLogger(__name__)
LOGO_PATH = Path(__file__).resolve().parent.parent / 'templates' / 'email' / 'logo-mark.png'


def send(to: str, subject: str, text: str, html: str, in_reply_to: str | None = None) -> bool:
    host, sender = os.getenv('SMTP_HOST'), os.getenv('SMTP_FROM')
    if not (host and sender):
        log.info('Email to %s not sent (SMTP not configured): %s', to, subject)
        return False
    display, address = parseaddr(sender)
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = sender if display else formataddr(('PhishGuard-AI', address))
    message['To'] = to
    message['Date'] = formatdate(localtime=True)
    message['Message-ID'] = make_msgid(domain=address.split('@')[-1] or None)
    message['Auto-Submitted'] = 'auto-replied'  # tells other robots not to answer (no mail loops)
    if in_reply_to:
        message['In-Reply-To'] = in_reply_to
        message['References'] = in_reply_to
    message.set_content(text)
    message.add_alternative(html, subtype='html')
    if LOGO_PATH.exists():
        message.get_payload()[1].add_related(LOGO_PATH.read_bytes(), 'image', 'png', cid=f'<{LOGO_CID}>',
                                             filename='logo.png')
    try:
        with smtplib.SMTP(host, int(os.getenv('SMTP_PORT', '587')), timeout=15) as smtp:
            if os.getenv('SMTP_USE_TLS', 'true').lower() == 'true':
                smtp.starttls()
            username, password = os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD')
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
        return True
    except Exception:
        log.exception('Email delivery to %s failed', to)
        return False
