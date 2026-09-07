# backend/app/api/auth.py

from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.services.verification_service import VerificationService
import bcrypt
import pyotp
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)
verification_service = VerificationService()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        if confirm_password is not None and password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Hash password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            is_admin=False,
            email_verified=False,
            auth_provider='password',
        )
        
        db.session.add(user)
        db.session.commit()
        token = secrets.token_urlsafe(32)
        verification_service.create_challenge(user.email, 'email_link', token)
        if not verification_service.send_verification_link(user.email, token):
            db.session.delete(user)
            db.session.commit()
            return jsonify({'error': 'Unable to send verification email'}), 502
        
        return jsonify({
            'message': 'Registration successful. Check your email to verify your account.',
            'requires_verification': True,
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.email_verified:
            return jsonify({
                'error': 'Email verification required',
                'requires_verification': True,
            }), 403
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            return jsonify({'error': 'Account locked. Try again later'}), 403
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            db.session.commit()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Reset login attempts
        user.login_attempts = 0
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        if user.mfa_active:
            session['mfa_pending_user_id'] = user.id
            return jsonify({'mfa_required': True}), 202

        login_user(user)
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'is_admin': current_user.is_admin,
        'mfa_active': current_user.mfa_active,
        'created_at': current_user.created_at.isoformat()
    }), 200


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
    return jsonify({'mfa_active': True}), 200


@auth_bp.route('/mfa/disable', methods=['POST'])
@login_required
def disable_mfa():
    current_user.mfa_active = False
    current_user.mfa_secret = None
    db.session.commit()
    return jsonify({'mfa_active': False}), 200


@auth_bp.route('/mfa/verify-login', methods=['POST'])
def verify_mfa_login():
    pending_user_id = session.get('mfa_pending_user_id')
    code = (request.get_json() or {}).get('code', '')
    user = db.session.get(User, pending_user_id) if pending_user_id else None
    if not user or not user.mfa_active or not user.mfa_secret:
        return jsonify({'error': 'No MFA login is pending'}), 400
    if not pyotp.TOTP(user.mfa_secret).verify(code):
        return jsonify({'error': 'Invalid authenticator code'}), 401
    session.pop('mfa_pending_user_id', None)
    login_user(user)
    return jsonify({
        'user': {'id': user.id, 'email': user.email, 'is_admin': user.is_admin}
    }), 200
