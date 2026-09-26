import logging
import secrets
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from pathlib import Path
from datetime import datetime, timedelta

import bcrypt
from flask import current_app

from app import db
from app.models import User, VerificationChallenge
from app.services.email_templates import LOGO_CID, verification_code_email

logger = logging.getLogger(__name__)

LOGO_PATH = Path(__file__).resolve().parent.parent / 'templates' / 'email' / 'logo-mark.png'


class VerificationService:
    """Generate email codes and provide a development-safe delivery hook."""

    def generate_code(self) -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    def create_challenge(self, destination: str, channel: str, value: str | None = None) -> str:
        code = value or self.generate_code()
        VerificationChallenge.query.filter_by(
            destination=destination,
            channel=channel,
            consumed_at=None,
        ).update({'consumed_at': datetime.utcnow()})
        challenge = VerificationChallenge(
            destination=destination,
            channel=channel,
            code_hash=bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        db.session.add(challenge)
        db.session.commit()
        return code

    def verify_challenge(self, destination: str, channel: str, code: str) -> bool:
        challenge = VerificationChallenge.query.filter_by(
            destination=destination,
            channel=channel,
            consumed_at=None,
        ).order_by(VerificationChallenge.created_at.desc()).first()
        if not challenge or challenge.expires_at < datetime.utcnow():
            return False
        if challenge.attempts >= 5:
            return False
        challenge.attempts += 1
        valid = bcrypt.checkpw(code.encode(), challenge.code_hash.encode())
        if valid:
            challenge.consumed_at = datetime.utcnow()
        db.session.commit()
        return valid

    def _build_code_email(self, email: str, code: str, sender: str) -> EmailMessage:
        """Branded HTML code email with a plain-text part and the logo embedded inline."""
        user = User.query.filter_by(email=email).first()
        name = (user.full_name if user and user.full_name else email.split('@')[0]).strip()
        subject, text, html = verification_code_email(name, code)

        # Show a display name ("PhishGuard-AI <x@gmail.com>") unless SMTP_FROM already has one
        display, address = parseaddr(sender)
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = sender if display else formataddr(('PhishGuard-AI', address))
        message['To'] = email
        message['Date'] = formatdate(localtime=True)
        message['Message-ID'] = make_msgid(domain=address.split('@')[-1] or None)
        message.set_content(text)
        message.add_alternative(html, subtype='html')
        if LOGO_PATH.exists():
            message.get_payload()[1].add_related(
                LOGO_PATH.read_bytes(), 'image', 'png', cid=f'<{LOGO_CID}>', filename='logo.png',
            )
        return message

    def send_verification_email(self, email: str, code: str) -> bool:
        host = os.getenv('SMTP_HOST')
        sender = os.getenv('SMTP_FROM')
        if host and sender:
            try:
                message = self._build_code_email(email, code, sender)
                with smtplib.SMTP(host, int(os.getenv('SMTP_PORT', '587')), timeout=10) as smtp:
                    if os.getenv('SMTP_USE_TLS', 'true').lower() == 'true':
                        smtp.starttls()
                    username = os.getenv('SMTP_USERNAME')
                    password = os.getenv('SMTP_PASSWORD')
                    if username and password:
                        smtp.login(username, password)
                    smtp.send_message(message)
                return True
            except Exception:
                logger.exception('Verification code email delivery failed')
                # Local development only: surface the code so sign-up isn't blocked by SMTP
                if current_app.debug:
                    logger.warning("SMTP failed - development code for %s: %s", email, code)
                    return True
                return False
        logger.info("Development email code for %s: %s", email, code)
        return True

    def send_verification_link(self, email: str, token: str) -> bool:
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        link = f'{frontend_url}/verify-email?email={email}&token={token}'
        host = os.getenv('SMTP_HOST')
        sender = os.getenv('SMTP_FROM')
        if host and sender:
            try:
                message = EmailMessage()
                message['Subject'] = 'Vérifiez votre adresse email PhishGuard-AI'
                message['From'] = sender
                message['To'] = email
                message.set_content(
                    f'Cliquez sur ce lien pour vérifier votre adresse email :\n\n{link}\n\n'
                    'Ce lien expire dans 5 minutes. Si vous n’avez pas créé ce compte, '
                    'ignorez cet email.'
                )
                with smtplib.SMTP(host, int(os.getenv('SMTP_PORT', '587')), timeout=10) as smtp:
                    if os.getenv('SMTP_USE_TLS', 'true').lower() == 'true':
                        smtp.starttls()
                    username = os.getenv('SMTP_USERNAME')
                    password = os.getenv('SMTP_PASSWORD')
                    if username and password:
                        smtp.login(username, password)
                    smtp.send_message(message)
                return True
            except Exception:
                logger.exception('Verification link email delivery failed')
                return False
        logger.info("Development verification link for %s: %s", email, link)
        return True

    def send_welcome_email(self, email: str) -> bool:
        logger.info("Development welcome email for %s", email)
        return True
