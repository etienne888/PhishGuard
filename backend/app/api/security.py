"""
Step-up authentication ("sudo mode") for sensitive admin actions.

Deleting an account, granting admin rights, changing platform policies or
removing a blocklist entry requires the admin to have re-entered their password
(and their authenticator code when MFA is on) within the last `sudo_minutes`.
A stolen session cookie alone is therefore not enough to cause lasting damage.

The frontend catches the SUDO_REQUIRED error, asks for the password, calls
POST /api/admin/security/sudo and replays the original request.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from functools import wraps

from flask import session

from app.api.responses import err


def sudo_active() -> bool:
    until = session.get('sudo_until')
    return bool(until) and datetime.utcnow().timestamp() < until


def grant_sudo(minutes: int) -> datetime:
    until = datetime.utcnow() + timedelta(minutes=minutes)
    session['sudo_until'] = until.timestamp()
    return until


def sudo_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not sudo_active():
            return err('SUDO_REQUIRED', 'Confirmez votre identité pour cette action sensible.', 403)
        return fn(*args, **kwargs)
    return wrapper
