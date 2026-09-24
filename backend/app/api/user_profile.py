"""Authenticated user's own profile: name, email, profile picture, password."""
from __future__ import annotations

import io
import os
import re

import bcrypt
from flask import Blueprint, current_app, request, send_file
from flask_login import current_user, login_required

from app import db
from app.api.responses import err, ok
from app.models import User

user_profile_bp = Blueprint('user_profile', __name__)

MAX_AVATAR_BYTES = 2 * 1024 * 1024
AVATAR_SIZE = 256
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _avatar_dir() -> str:
    path = os.path.join(current_app.instance_path, 'avatars')
    os.makedirs(path, exist_ok=True)
    return path


def _avatar_path(user_id: int) -> str:
    return os.path.join(_avatar_dir(), f'{int(user_id)}.png')


def _serialize(user: User) -> dict:
    has_avatar = os.path.exists(_avatar_path(user.id))
    version = int(os.path.getmtime(_avatar_path(user.id))) if has_avatar else None
    return {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'phone': user.phone_number,
        'email_verified': bool(user.email_verified),
        'mfa_active': bool(user.mfa_active),
        'auth_provider': user.auth_provider,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        # ?v= busts the browser cache after a new upload
        'avatar_url': f'/api/user/avatar/{user.id}?v={version}' if has_avatar else None,
    }


def _check_password(password: str | None) -> bool:
    if not password or not current_user.password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), current_user.password_hash.encode('utf-8'))
    except ValueError:
        return False


@user_profile_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    return ok(_serialize(current_user))


@user_profile_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}

    if 'full_name' in data:
        name = (data.get('full_name') or '').strip()
        if len(name) > 255:
            return err('INVALID_NAME', 'Nom trop long (255 caractères maximum).')
        current_user.full_name = name or None

    new_email = (data.get('email') or '').strip().lower()
    if new_email and new_email != current_user.email:
        if not EMAIL_RE.match(new_email):
            return err('INVALID_EMAIL', 'Adresse e-mail invalide.')
        # Changing the login identifier requires the current password
        if not _check_password(data.get('current_password')):
            return err('INVALID_PASSWORD', 'Mot de passe actuel incorrect.', 403)
        if User.query.filter(User.email == new_email, User.id != current_user.id).first():
            return err('EMAIL_TAKEN', 'Cette adresse e-mail est déjà utilisée.', 409)
        current_user.email = new_email
        current_user.email_verified = False

    db.session.commit()
    return ok(_serialize(current_user))


@user_profile_bp.route('/profile/password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    if not _check_password(data.get('current_password')):
        return err('INVALID_PASSWORD', 'Mot de passe actuel incorrect.', 403)
    new_password = data.get('new_password') or ''
    if len(new_password) < 8:
        return err('WEAK_PASSWORD', 'Le nouveau mot de passe doit contenir au moins 8 caractères.')
    current_user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.session.commit()
    return ok({'changed': True})


@user_profile_bp.route('/profile/avatar', methods=['POST'])
@login_required
def upload_avatar():
    from PIL import Image, UnidentifiedImageError

    upload = request.files.get('file')
    if upload is None:
        return err('NO_FILE', 'Aucune image reçue.')
    raw = upload.read(MAX_AVATAR_BYTES + 1)
    if len(raw) > MAX_AVATAR_BYTES:
        return err('FILE_TOO_LARGE', 'Image trop volumineuse (2 Mo maximum).')
    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()                      # rejects truncated / non-image files
        image = Image.open(io.BytesIO(raw))  # verify() invalidates the object
        if image.format not in {'PNG', 'JPEG', 'WEBP'}:
            return err('INVALID_IMAGE', 'Formats acceptés : PNG, JPEG ou WEBP.')
    except (UnidentifiedImageError, OSError):
        return err('INVALID_IMAGE', "Ce fichier n'est pas une image valide.")

    # Re-encode as a square PNG: strips metadata and any embedded payload
    image = image.convert('RGBA')
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    image = image.crop((left, top, left + side, top + side)).resize((AVATAR_SIZE, AVATAR_SIZE))
    image.save(_avatar_path(current_user.id), format='PNG')
    return ok(_serialize(current_user))


@user_profile_bp.route('/profile/avatar', methods=['DELETE'])
@login_required
def delete_avatar():
    path = _avatar_path(current_user.id)
    if os.path.exists(path):
        os.remove(path)
    return ok(_serialize(current_user))


@user_profile_bp.route('/avatar/<int:user_id>', methods=['GET'])
@login_required
def get_avatar(user_id: int):
    path = _avatar_path(user_id)
    if not os.path.exists(path):
        return err('NOT_FOUND', 'Aucune photo de profil.', 404)
    return send_file(path, mimetype='image/png', max_age=3600)
