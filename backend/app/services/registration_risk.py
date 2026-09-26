"""
Sign-up risk scoring (fraud & abuse prevention).

Each new account gets a 0-100 risk score from explainable signals. Depending on
the `registration_mode` setting the account is approved immediately or waits
for an administrator (who sees the same flags in User management).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.models import User

# Throw-away mailbox providers commonly used for fake accounts
DISPOSABLE_DOMAINS = {
    'mailinator.com', 'yopmail.com', 'yopmail.fr', 'guerrillamail.com', 'guerrillamail.info', '10minutemail.com',
    'tempmail.com', 'temp-mail.org', 'trashmail.com', 'getnada.com', 'dispostable.com', 'sharklasers.com',
    'maildrop.cc', 'throwawaymail.com', 'fakeinbox.com', 'mintemail.com', 'moakt.com', 'emailondeck.com',
    'mohmal.com', 'tempail.com', 'tempr.email', 'discard.email', 'mailnesia.com', 'spamgourmet.com',
}

# Weight of each flag in the 0-100 score
WEIGHTS = {
    'disposable_email': 45,
    'ip_reuse': 25,          # several accounts from the same IP in 24 h
    'ip_burst': 20,          # many sign-ups platform-wide in the last 10 min (bot wave)
    'anonymizer': 30,        # VPN / proxy / Tor exit
    'datacenter_ip': 20,     # hosting provider rather than a home / mobile connection
    'foreign_ip': 10,        # outside Cameroon (informational for a national service)
    'bot_trap': 60,          # hidden form field filled in (only bots see it)
    'too_fast': 25,          # form submitted faster than a human can type
    'name_mismatch': 10,     # name looks random / contains digits
}


def assess(email: str, ip: str | None, geo: dict, full_name: str | None,
           honeypot: str | None, fill_seconds: float | None) -> tuple[int, list[dict]]:
    """Return (score, flags) where each flag is {code, weight, detail}."""
    flags: list[dict] = []

    def flag(code: str, detail: str = ''):
        flags.append({'code': code, 'weight': WEIGHTS[code], 'detail': detail})

    domain = email.rsplit('@', 1)[-1].lower()
    if domain in DISPOSABLE_DOMAINS:
        flag('disposable_email', domain)

    if ip:
        day_ago = datetime.utcnow() - timedelta(hours=24)
        same_ip = User.query.filter(User.registration_ip == ip, User.created_at >= day_ago).count()
        if same_ip >= 2:
            flag('ip_reuse', str(same_ip))
    recent = User.query.filter(User.created_at >= datetime.utcnow() - timedelta(minutes=10)).count()
    if recent >= 10:
        flag('ip_burst', str(recent))

    if geo.get('proxy'):
        flag('anonymizer', geo.get('isp') or '')
    elif geo.get('hosting'):
        flag('datacenter_ip', geo.get('isp') or '')
    if geo.get('country_code') and geo.get('country_code') != 'CM':
        flag('foreign_ip', geo.get('country') or geo.get('country_code'))

    if honeypot:
        flag('bot_trap')
    if fill_seconds is not None and fill_seconds < 3:
        flag('too_fast', f'{fill_seconds:.1f}s')
    if full_name and (any(ch.isdigit() for ch in full_name) or len(full_name.replace(' ', '')) < 3):
        flag('name_mismatch', full_name)

    return min(100, sum(f['weight'] for f in flags)), flags


def decide(score: int, mode: str, threshold: int) -> str:
    """Initial approval_status for a new account."""
    if mode == 'approval':
        return 'pending'
    if mode == 'risk_based' and score >= threshold:
        return 'pending'
    return 'approved'
