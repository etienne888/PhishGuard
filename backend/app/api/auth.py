# backend/app/api/auth.py

from flask import Blueprint, current_app, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.services.verification_service import VerificationService
from app.services import audit_service, registration_risk, settings_service
from app.services.client_info import client_ip, geolocate, user_agent
import bcrypt
import pyotp
import secrets
import time
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)
verification_service = VerificationService()

# Messages the frontend maps to translated text (stores/auth.ts)
APPROVAL_ERRORS = {
    'pending': 'Account pending approval',
    'review': 'Account under verification',
    'rejected': 'Account rejected',
}
CAMEROON_REGIONS = {'adamaoua', 'centre', 'est', 'extreme-nord', 'littoral', 'nord', 'nord-ouest',
                    'ouest', 'sud', 'sud-ouest', 'diaspora'}


def _public_user(user: User) -> dict:
    return {'id': user.id, 'email': user.email, 'is_admin': user.is_admin}


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user: validation, sign-up risk scoring, approval policy, email code."""
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        phone = (data.get('phone') or '').strip() or None
        full_name = ' '.join((data.get('full_name') or '').split())[:255] or None
        region = (data.get('region') or '').strip().lower() or None
        city = ' '.join((data.get('city') or '').split())[:120] or None

        if not settings_service.get('allow_signup'):
            return jsonify({'error': 'New account registration is currently disabled'}), 403

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        if not full_name or len(full_name) < 2:
            return jsonify({'error': 'Full name required'}), 400
        if region and region not in CAMEROON_REGIONS:
            return jsonify({'error': 'Unknown region'}), 400
        if not data.get('acceptTerms'):
            return jsonify({'error': 'Terms must be accepted'}), 400
        if confirm_password is not None and password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        if len(password) < settings_service.get('password_min_length'):
            return jsonify({'error': f"Password must be at least {settings_service.get('password_min_length')} characters"}), 400

        existing_user = User.query.filter_by(email=email).first()
        # Sign-up verification is by 6-digit OTP code only (no email link)
        if existing_user and not existing_user.email_verified:
            code = verification_service.create_challenge(email, 'email')
            email_sent = verification_service.send_verification_email(email, code)
            return jsonify({
                'message': 'Verification code sent. Check your email to verify your account.',
                'requires_verification': True,
                'verification_email_sent': email_sent,
            }), 200
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        if phone and User.query.filter_by(phone_number=phone).first():
            return jsonify({'error': 'Phone number already registered'}), 400

        # Who is signing up: IP, device, approximate location, risk signals
        ip = client_ip()
        geo = geolocate(ip)
        started = data.get('form_started_at')
        fill_seconds = (time.time() * 1000 - started) / 1000 if isinstance(started, (int, float)) else None
        risk, flags = registration_risk.assess(email, ip, geo, full_name, data.get('website'), fill_seconds)
        if settings_service.get('block_disposable_emails') and any(f['code'] == 'disposable_email' for f in flags):
            audit_service.record('registration_blocked', details={'email': email, 'flags': flags}, severity='warning')
            return jsonify({'error': 'Disposable email not allowed'}), 400
        if any(f['code'] == 'bot_trap' for f in flags):
            # Pretend success to the bot, create nothing
            audit_service.record('registration_blocked', details={'email': email, 'flags': flags}, severity='warning')
            return jsonify({'message': 'Registration successful.', 'requires_verification': True,
                            'verification_email_sent': True}), 201

        approval = registration_risk.decide(risk, settings_service.get('registration_mode'),
                                            settings_service.get('registration_risk_threshold'))
        user = User(
            email=email, phone_number=phone, full_name=full_name, region=region, city=city,
            password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            is_admin=False, email_verified=False, auth_provider='password',
            approval_status=approval, terms_accepted_at=datetime.utcnow(), password_changed_at=datetime.utcnow(),
            registration_ip=ip, registration_user_agent=user_agent(), registration_geo=geo or None,
            risk_score=risk, risk_flags=flags,
        )
        db.session.add(user)
        db.session.commit()
        audit_service.record('registration_flagged' if approval != 'approved' else 'registration',
                             user_id=user.id, details={'risk': risk, 'flags': [f['code'] for f in flags],
                                                       'approval': approval})

        code = verification_service.create_challenge(user.email, 'email')
        email_sent = verification_service.send_verification_email(user.email, code)
        return jsonify({
            'message': 'Registration successful. Check your email to verify your account.',
            'requires_verification': True,
            'verification_email_sent': email_sent,
            'approval_status': approval,
        }), 201

    except Exception:
        current_app.logger.exception('Registration failed')
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Password login with lockout, approval gate, MFA step and full audit trail."""
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Same answer and similar timing as a wrong password: no account enumeration
            bcrypt.checkpw(b'timing-equalizer', bcrypt.hashpw(b'x', bcrypt.gensalt(4)))
            audit_service.record('login_failed', details={'email': email, 'reason': 'unknown_account'})
            return jsonify({'error': 'Invalid credentials'}), 401

        if user.locked_until and user.locked_until > datetime.utcnow():
            audit_service.record('login_blocked', user_id=user.id, details={'reason': 'locked'})
            return jsonify({'error': 'Account locked. Try again later'}), 403

        # Password first: nothing about the account is revealed before it is proven
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            user.login_attempts = (user.login_attempts or 0) + 1
            locked = user.login_attempts >= settings_service.get('max_login_attempts')
            if locked:
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings_service.get('lockout_duration_min'))
            db.session.commit()
            audit_service.record('account_locked' if locked else 'login_failed', user_id=user.id,
                                 details={'attempts': user.login_attempts})
            return jsonify({'error': 'Invalid credentials'}), 401

        if user.status == 'suspended':
            audit_service.record('login_blocked', user_id=user.id, details={'reason': 'suspended'})
            return jsonify({'error': 'This account has been suspended. Contact an administrator.'}), 403

        if not user.email_verified:
            code = verification_service.create_challenge(user.email, 'email')
            verification_service.send_verification_email(user.email, code)
            return jsonify({'error': 'Email verification required', 'requires_verification': True}), 403

        if (user.approval_status or 'approved') != 'approved':
            audit_service.record('login_blocked', user_id=user.id, details={'reason': user.approval_status})
            return jsonify({'error': APPROVAL_ERRORS.get(user.approval_status, 'Account pending approval'),
                            'approval_status': user.approval_status, 'note': user.approval_note}), 403

        user.login_attempts = 0
        db.session.commit()

        if user.mfa_active:
            session['mfa_pending_user_id'] = user.id
            return jsonify({'mfa_required': True}), 202

        return _complete_login(user, method='password')

    except Exception:
        current_app.logger.exception('Login failed')
        db.session.rollback()
        return jsonify({'error': 'Login failed'}), 500


def _complete_login(user: User, method: str):
    """Open the session and record the login (flags logins from a new IP + country)."""
    ip = client_ip()
    geo = geolocate(ip)
    new_location = audit_service.is_new_location(user.id, ip, geo.get('country'))
    user.last_login = datetime.utcnow()
    user.last_login_ip = ip
    db.session.commit()
    session.pop('sudo_until', None)
    login_user(user)
    audit_service.record('login_success', user_id=user.id, actor_id=user.id,
                         details={'method': method, 'new_location': new_location},
                         severity='warning' if new_location else 'info')
    return jsonify({
        'message': 'Login successful',
        'user': _public_user(user),
        # Platform policy requires MFA but this account has none yet: send the user to Security
        'mfa_setup_required': bool(settings_service.get('mfa_required') and not user.mfa_active),
        'new_location': new_location,
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    audit_service.record('logout', user_id=current_user.id)
    logout_user()
    session.pop('sudo_until', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'displayName': current_user.full_name,
        'is_admin': current_user.is_admin,
        'mfa_active': current_user.mfa_active,
        'avatar_url': f'/api/user/avatar/{current_user.id}' if _has_avatar(current_user.id) else None,
        'onboarded': current_user.onboarded_at is not None,
        'created_at': current_user.created_at.isoformat()
    }), 200


def _has_avatar(user_id: int) -> bool:
    try:
        from app.api.user_profile import _avatar_path
        import os
        return os.path.exists(_avatar_path(user_id))
    except Exception:
        return False


@auth_bp.route('/mfa/setup', methods=['POST'])
@login_required
def setup_mfa():
    if not current_user.mfa_secret:
        current_user.mfa_secret = pyotp.random_base32()
        db.session.commit()
    uri = pyotp.TOTP(current_user.mfa_secret).provisioning_uri(
        name=current_user.email,
        issuer_name='PhishGuard-AI',
    )
    return jsonify({'secret': current_user.mfa_secret, 'otpauth_uri': uri}), 200


@auth_bp.route('/mfa/enable', methods=['POST'])
@login_required
def enable_mfa():
    code = (request.get_json() or {}).get('code', '')
    if not current_user.mfa_secret or not pyotp.TOTP(current_user.mfa_secret).verify(code):
        return jsonify({'error': 'Invalid authenticator code'}), 400
    current_user.mfa_active = True
    db.session.commit()
    audit_service.record('mfa_enabled', user_id=current_user.id)
    return jsonify({'mfa_active': True}), 200


@auth_bp.route('/mfa/disable', methods=['POST'])
@login_required
def disable_mfa():
    # Removing a factor is itself protected by that factor
    code = (request.get_json(silent=True) or {}).get('code', '')
    if current_user.mfa_active and current_user.mfa_secret and not pyotp.TOTP(current_user.mfa_secret).verify(code):
        audit_service.record('mfa_failed', user_id=current_user.id, details={'during': 'disable'})
        return jsonify({'error': 'Invalid authenticator code'}), 400
    current_user.mfa_active = False
    current_user.mfa_secret = None
    db.session.commit()
    audit_service.record('mfa_disabled', user_id=current_user.id)
    return jsonify({'mfa_active': False}), 200


@auth_bp.route('/mfa/verify-login', methods=['POST'])
def verify_mfa_login():
    pending_user_id = session.get('mfa_pending_user_id')
    code = (request.get_json() or {}).get('code', '')
    user = db.session.get(User, pending_user_id) if pending_user_id else None
    if not user or not user.mfa_active or not user.mfa_secret:
        return jsonify({'error': 'No MFA login is pending'}), 400
    if not pyotp.TOTP(user.mfa_secret).verify(code):
        audit_service.record('mfa_failed', user_id=user.id, details={'during': 'login'})
        return jsonify({'error': 'Invalid authenticator code'}), 401
    session.pop('mfa_pending_user_id', None)
    return _complete_login(user, method='password+totp')
