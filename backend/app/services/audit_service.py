"""
Security & audit trail.

Every sensitive event goes through record(): logins (success / failure / MFA),
password and MFA changes, and every admin action (approve a user, change a
setting, block a domain…). The admin audit log and each user's login history
are views on the same `security_events` table.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from flask_login import current_user

from app import db
from app.models import SecurityEvent
from app.services.client_info import client_ip, geolocate, user_agent

logger = logging.getLogger(__name__)

# Events that also deserve attention in the admin alert feed
WARNING_EVENTS = {'login_failed', 'mfa_failed', 'login_blocked', 'account_locked', 'mfa_disabled',
                  'registration_flagged', 'sudo_failed'}
CRITICAL_EVENTS = {'account_locked', 'admin_role_granted', 'admin_user_deleted'}


def record(event_type: str, user_id: int | None = None, details: dict | None = None,
           actor_id: int | None = None, severity: str | None = None, commit: bool = True) -> SecurityEvent | None:
    """Store one event with the caller's IP, device and approximate location. Never raises."""
    try:
        if actor_id is None and current_user and getattr(current_user, 'is_authenticated', False):
            actor_id = current_user.id
        ip = client_ip()
        event = SecurityEvent(
            event_type=event_type,
            severity=severity or ('critical' if event_type in CRITICAL_EVENTS
                                  else 'warning' if event_type in WARNING_EVENTS else 'info'),
            user_id=user_id, actor_id=actor_id, ip=ip, user_agent=user_agent(),
            geo=geolocate(ip) or None, details=details or None,
        )
        db.session.add(event)
        if commit:
            db.session.commit()
        return event
    except Exception:  # auditing must never break the action being audited
        logger.exception('Could not record security event %s', event_type)
        db.session.rollback()
        return None


def recent_failures(user_id: int, minutes: int = 60) -> int:
    since = datetime.utcnow() - timedelta(minutes=minutes)
    return SecurityEvent.query.filter(SecurityEvent.user_id == user_id,
                                      SecurityEvent.event_type.in_(('login_failed', 'mfa_failed')),
                                      SecurityEvent.created_at >= since).count()


def is_new_location(user_id: int, ip: str | None, country: str | None) -> bool:
    """True when this account never logged in from this IP nor this country before."""
    if not ip:
        return False
    previous = (SecurityEvent.query.filter_by(user_id=user_id, event_type='login_success')
                .order_by(SecurityEvent.created_at.desc()).limit(50).all())
    if not previous:
        return False  # first login ever: nothing to compare with
    if any(e.ip == ip for e in previous):
        return False
    return bool(country) and all((e.geo or {}).get('country') != country for e in previous)


def serialize(event: SecurityEvent, users: dict[int, str] | None = None) -> dict:
    from app.services.client_info import describe_device
    users = users or {}
    geo = event.geo or {}
    return {
        'id': event.id,
        'type': event.event_type,
        'severity': event.severity,
        'user_id': event.user_id,
        'user': users.get(event.user_id),
        'actor_id': event.actor_id,
        'actor': users.get(event.actor_id),
        'ip': event.ip,
        'device': describe_device(event.user_agent),
        'location': 'local' if geo.get('local') else ', '.join(filter(None, (geo.get('city'), geo.get('country')))) or None,
        'network': {'proxy': geo.get('proxy', False), 'hosting': geo.get('hosting', False), 'isp': geo.get('isp')},
        'details': event.details or {},
        'created_at': event.created_at.isoformat() if event.created_at else None,
    }
