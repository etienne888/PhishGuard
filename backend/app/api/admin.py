"""Admin-only platform control: user management, platform settings, admin profile."""
from __future__ import annotations

from functools import wraps

from flask import request
from flask import Blueprint
from flask_login import current_user, login_required

from datetime import datetime

from app import db
from app.api.responses import ok, err
from app.api.security import sudo_required
from app.models import User, Analysis, SecurityEvent
from app.services import audit_service, settings_service
from app.services.client_info import describe_device

APPROVAL_STATUSES = {'approved', 'pending', 'review', 'rejected'}
# Policy keys whose change weakens or strengthens the whole platform: need re-authentication
SENSITIVE_SETTINGS = {'allow_signup', 'require_email_verification', 'mfa_required', 'registration_mode',
                      'password_min_length', 'max_login_attempts', 'triage_mode', 'auto_block_incidents'}

admin_bp = Blueprint('admin', __name__)


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            return err('FORBIDDEN', 'Accès administrateur requis.', 403)
        return fn(*args, **kwargs)
    return wrapper


def _serialize_user(user: User) -> dict:
    threat_count = Analysis.query.filter_by(user_id=user.id, verdict='phishing').count()
    analyses_count = Analysis.query.filter_by(user_id=user.id).count()
    return {
        'id': user.id,
        'name': user.full_name or user.email.split('@')[0],
        'email': user.email,
        'phone': user.phone_number,
        'role': 'admin' if user.is_admin else 'user',
        'status': user.status or 'active',
        'mfa_enabled': bool(user.mfa_active),
        'email_verified': bool(user.email_verified),
        'auth_provider': user.auth_provider,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'locked': bool(user.locked_until),
        'threat_count': threat_count,
        'analyses_count': analyses_count,
        'job_title': user.job_title,
        'organization': user.organization,
        'region': user.region,
        'city': user.city,
        'approval_status': user.approval_status or 'approved',
        'approval_note': user.approval_note,
        'approved_at': user.approved_at.isoformat() if user.approved_at else None,
        'risk_score': user.risk_score or 0,
        'risk_flags': user.risk_flags or [],
        'registration': {
            'ip': user.registration_ip,
            'device': describe_device(user.registration_user_agent),
            'user_agent': user.registration_user_agent,
            'geo': user.registration_geo or {},
            'terms_accepted_at': user.terms_accepted_at.isoformat() if user.terms_accepted_at else None,
        },
        'last_login_ip': user.last_login_ip,
        'failed_logins': user.login_attempts or 0,
        'locked_until': user.locked_until.isoformat() if user.locked_until and user.locked_until > datetime.utcnow() else None,
        'has_avatar': _has_avatar(user.id),
    }


def _has_avatar(user_id: int) -> bool:
    import os
    from app.api.user_profile import _avatar_path
    return os.path.exists(_avatar_path(user_id))


def _get_user_or_404(user_id: int):
    user = db.session.get(User, user_id)
    return user, (None if user else err('NOT_FOUND', 'Utilisateur introuvable.', 404))


# ---------------------------------------------------------------- Users ----

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return ok({'items': [_serialize_user(u) for u in users], 'total': len(users)})


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err('NOT_FOUND', 'Utilisateur introuvable.', 404)
    return ok(_serialize_user(user))


@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
@admin_required
def update_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err('NOT_FOUND', 'Utilisateur introuvable.', 404)
    data = request.get_json() or {}
    if 'role' in data:
        from app.api.security import sudo_active
        if not sudo_active():
            return err('SUDO_REQUIRED', 'Confirmez votre identité pour cette action sensible.', 403)
        if user.id == current_user.id and data['role'] != 'admin':
            return err('INVALID_OPERATION', 'Vous ne pouvez pas retirer vos propres droits admin.', 400)
        was_admin = user.is_admin
        user.is_admin = data['role'] == 'admin'
        if user.is_admin != was_admin:
            audit_service.record('admin_role_granted' if user.is_admin else 'admin_role_revoked',
                                 user_id=user.id, commit=False)
    if 'full_name' in data:
        user.full_name = (data['full_name'] or '').strip() or None
    if 'status' in data and data['status'] in {'active', 'suspended'}:
        user.status = data['status']
    db.session.commit()
    return ok(_serialize_user(user))


@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@admin_required
def suspend_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err('NOT_FOUND', 'Utilisateur introuvable.', 404)
    if user.id == current_user.id:
        return err('INVALID_OPERATION', 'Vous ne pouvez pas vous suspendre vous-même.', 400)
    user.status = 'suspended'
    user.session_version = (user.session_version or 1) + 1  # end their sessions now
    db.session.commit()
    audit_service.record('admin_user_suspended', user_id=user.id, severity='warning')
    return ok(_serialize_user(user))


@admin_bp.route('/users/<int:user_id>/reactivate', methods=['POST'])
@admin_required
def reactivate_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err('NOT_FOUND', 'Utilisateur introuvable.', 404)
    user.status = 'active'
    user.login_attempts = 0
    user.locked_until = None
    db.session.commit()
    audit_service.record('admin_user_reactivated', user_id=user.id)
    return ok(_serialize_user(user))


@admin_bp.route('/users/<int:user_id>/force-logout', methods=['POST'])
@admin_required
def force_logout(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err('NOT_FOUND', 'Utilisateur introuvable.', 404)
    # Session ids embed session_version (User.get_id): bumping it invalidates
    # every cookie of this account on its next request.
    user.session_version = (user.session_version or 1) + 1
    db.session.commit()
    audit_service.record('admin_force_logout', user_id=user.id, severity='warning')
    return ok({'ok': True})


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
@sudo_required
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err('NOT_FOUND', 'Utilisateur introuvable.', 404)
    if user.id == current_user.id:
        return err('INVALID_OPERATION', 'Vous ne pouvez pas supprimer votre propre compte.', 400)
    email = user.email
    # Keep the user's analyses (anonymised) for statistics and training
    Analysis.query.filter_by(user_id=user.id).update({'user_id': None})
    db.session.delete(user)
    db.session.commit()
    audit_service.record('admin_user_deleted', details={'email': email})
    return ok({'deleted': True})


# ---------------------------------------------------- Approval workflow ----

@admin_bp.route('/users/<int:user_id>/approval', methods=['POST'])
@admin_required
def set_approval(user_id: int):
    """approve | reject | review (ask for further verification), with an optional note shown to the user."""
    user, missing = _get_user_or_404(user_id)
    if missing:
        return missing
    data = request.get_json(silent=True) or {}
    decision = {'approve': 'approved', 'reject': 'rejected', 'review': 'review'}.get(data.get('decision'))
    if not decision:
        return err('INVALID_DECISION', "Décision attendue : 'approve', 'reject' ou 'review'.")
    if user.id == current_user.id:
        return err('INVALID_OPERATION', 'Vous ne pouvez pas modifier votre propre validation.', 400)
    user.approval_status = decision
    user.approval_note = (data.get('note') or '')[:1000] or None
    user.approved_by = current_user.id
    user.approved_at = datetime.utcnow()
    if decision != 'approved':
        user.session_version = (user.session_version or 1) + 1
    if data.get('resend_code') and decision == 'review':
        # Further verification: the user must prove the mailbox again
        from app.services.verification_service import VerificationService
        service = VerificationService()
        user.email_verified = False
        service.send_verification_email(user.email, service.create_challenge(user.email, 'email'))
    db.session.commit()
    audit_service.record(f'admin_user_{decision}', user_id=user.id, details={'note': user.approval_note},
                         severity='warning' if decision == 'rejected' else 'info')
    return ok(_serialize_user(user))


@admin_bp.route('/users/<int:user_id>/unlock', methods=['POST'])
@admin_required
def unlock_user(user_id: int):
    user, missing = _get_user_or_404(user_id)
    if missing:
        return missing
    user.locked_until, user.login_attempts = None, 0
    db.session.commit()
    audit_service.record('admin_user_unlocked', user_id=user.id)
    return ok(_serialize_user(user))


@admin_bp.route('/users/<int:user_id>/activity', methods=['GET'])
@admin_required
def user_activity(user_id: int):
    """Login history + security events + accounts sharing the registration IP."""
    user, missing = _get_user_or_404(user_id)
    if missing:
        return missing
    events = (SecurityEvent.query.filter(SecurityEvent.user_id == user.id)
              .order_by(SecurityEvent.created_at.desc()).limit(40).all())
    ids = {e.actor_id for e in events if e.actor_id} | {user.id}
    names = {u.id: u.email for u in User.query.filter(User.id.in_(ids)).all()}
    siblings = []
    if user.registration_ip:
        siblings = [{'id': u.id, 'email': u.email, 'status': u.status, 'approval_status': u.approval_status}
                    for u in User.query.filter(User.registration_ip == user.registration_ip, User.id != user.id)
                    .limit(20).all()]
    distinct_ips = {e.ip for e in events if e.event_type == 'login_success' and e.ip}
    return ok({
        'events': [audit_service.serialize(e, names) for e in events],
        'same_ip_accounts': siblings,
        'distinct_login_ips': len(distinct_ips),
        'failed_logins_24h': audit_service.recent_failures(user.id, minutes=24 * 60),
    })


# --------------------------------------------------------------- Stats -----

@admin_bp.route('/stats/overview', methods=['GET'])
@admin_required
def stats_overview():
    return ok({
        'pending_approval': User.query.filter(User.approval_status.in_(('pending', 'review'))).count(),
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(status='active').count(),
        'suspended_users': User.query.filter_by(status='suspended').count(),
        'admin_users': User.query.filter_by(is_admin=True).count(),
        'mfa_enabled_users': User.query.filter_by(mfa_active=True).count(),
        'total_analyses': Analysis.query.count(),
        'phishing_detected': Analysis.query.filter_by(verdict='phishing').count(),
    })


# ------------------------------------------------------------- Profile -----

@admin_bp.route('/profile', methods=['GET'])
@admin_required
def get_profile():
    return ok(_serialize_user(current_user))


@admin_bp.route('/profile', methods=['PUT'])
@admin_required
def update_profile():
    data = request.get_json() or {}
    if 'full_name' in data:
        current_user.full_name = (data['full_name'] or '').strip() or None
    if 'phone' in data:
        phone = (data['phone'] or '').strip() or None
        if phone and User.query.filter(User.phone_number == phone, User.id != current_user.id).first():
            return err('CONFLICT', 'Ce numéro est déjà utilisé.', 409)
        current_user.phone_number = phone
    for field, size in (('job_title', 120), ('organization', 160), ('city', 120)):
        if field in data:
            setattr(current_user, field, ' '.join((data[field] or '').split())[:size] or None)
    db.session.commit()
    audit_service.record('admin_profile_updated', user_id=current_user.id, details={'fields': sorted(data)})
    return ok(_serialize_user(current_user))


# ------------------------------------------------------------- Settings ----

@admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_settings():
    return ok(settings_service.get_settings())


@admin_bp.route('/settings', methods=['PUT'])
@admin_required
def update_settings():
    from app.api.security import sudo_active
    data = request.get_json() or {}
    before = settings_service.get_settings()
    changed = {k: v for k, v in data.items() if k in before and before[k] != v}
    if set(changed) & SENSITIVE_SETTINGS and not sudo_active():
        return err('SUDO_REQUIRED', 'Confirmez votre identité pour modifier cette politique.', 403)
    result = settings_service.update_settings(data)
    if changed:
        audit_service.record('admin_settings_changed', details={
            k: {'from': before[k], 'to': result.get(k)} for k in changed},
            severity='warning' if set(changed) & SENSITIVE_SETTINGS else 'info')
    if {'triage_mode', 'triage_threshold'} & set(changed):
        from app.services.triage_service import run_all
        run_all()  # apply the new automation policy to the queue right away
    return ok(result)
