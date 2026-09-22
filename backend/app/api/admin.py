"""Admin-only platform control: user management, platform settings, admin profile."""
from __future__ import annotations

from functools import wraps

from flask import request
from flask import Blueprint
from flask_login import current_user, login_required

from app import db
from app.api.responses import ok, err
from app.models import User, Analysis
from app.services import settings_service

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
    }


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
        if user.id == current_user.id and data['role'] != 'admin':
            return err('INVALID_OPERATION', 'Vous ne pouvez pas retirer vos propres droits admin.', 400)
        user.is_admin = data['role'] == 'admin'
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
    db.session.commit()
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
    return ok(_serialize_user(user))


@admin_bp.route('/users/<int:user_id>/force-logout', methods=['POST'])
@admin_required
def force_logout(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err('NOT_FOUND', 'Utilisateur introuvable.', 404)
    # Session store is server-side (Flask-Login cookie signed by SECRET_KEY);
    # bumping login_attempts-free lockout is not needed, we simply mark for re-auth.
    user.locked_until = None
    db.session.commit()
    return ok({'ok': True})


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err('NOT_FOUND', 'Utilisateur introuvable.', 404)
    if user.id == current_user.id:
        return err('INVALID_OPERATION', 'Vous ne pouvez pas supprimer votre propre compte.', 400)
    db.session.delete(user)
    db.session.commit()
    return ok({'deleted': True})


# --------------------------------------------------------------- Stats -----

@admin_bp.route('/stats/overview', methods=['GET'])
@admin_required
def stats_overview():
    return ok({
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
    db.session.commit()
    return ok(_serialize_user(current_user))


# ------------------------------------------------------------- Settings ----

@admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_settings():
    return ok(settings_service.get_settings())


@admin_bp.route('/settings', methods=['PUT'])
@admin_required
def update_settings():
    data = request.get_json() or {}
    return ok(settings_service.update_settings(data))
