"""Platform-wide security & auth settings, persisted as key/value rows.

Backed by the `platform_settings` table so admins can change platform
behaviour (signup, MFA, lockout policy, password policy) without a redeploy.
"""
from __future__ import annotations

from app import db
from app.models import PlatformSetting

DEFAULTS: dict[str, str] = {
    'allow_signup': 'true',
    'require_email_verification': 'true',
    'mfa_required': 'false',
    'session_timeout_min': '30',
    'max_login_attempts': '5',
    'lockout_duration_min': '15',
    'password_min_length': '12',
    'password_require_upper': 'true',
    'password_require_number': 'true',
    'password_require_symbol': 'true',
}

_BOOL_KEYS = {
    'allow_signup', 'require_email_verification', 'mfa_required',
    'password_require_upper', 'password_require_number', 'password_require_symbol',
}
_INT_KEYS = {
    'session_timeout_min', 'max_login_attempts', 'lockout_duration_min', 'password_min_length',
}


def _cast(key: str, raw: str):
    if key in _BOOL_KEYS:
        return str(raw).lower() == 'true'
    if key in _INT_KEYS:
        return int(raw)
    return raw


def get_settings() -> dict:
    rows = {row.key: row.value for row in PlatformSetting.query.all()}
    merged = {**DEFAULTS, **rows}
    return {key: _cast(key, value) for key, value in merged.items()}


def get(key: str):
    return get_settings().get(key, _cast(key, DEFAULTS.get(key, '')))


def update_settings(patch: dict) -> dict:
    for key, value in patch.items():
        if key not in DEFAULTS:
            continue
        str_value = 'true' if value is True else 'false' if value is False else str(value)
        row = db.session.get(PlatformSetting, key)
        if row:
            row.value = str_value
        else:
            db.session.add(PlatformSetting(key=key, value=str_value))
    db.session.commit()
    return get_settings()
