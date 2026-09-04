"""
OAuth Routes (Google, WhatsApp)
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user
from app import db
from app.models import User
from app.services.oauth_service import OAuthService
from app.services.otp_service import OTPService
import secrets

oauth_bp = Blueprint('oauth', __name__)
oauth_service = OAuthService()
otp_service = OTPService()


def _create_oauth_user(email: str) -> User:
    """Create a new local user for OAuth login."""
    user = User()
    user.email = email
    user.password_hash = secrets.token_urlsafe(32)
    user.is_admin = False

    db.session.add(user)  # type: ignore[attr-defined]
    db.session.commit()  # type: ignore[attr-defined]
    return user


@oauth_bp.route('/google/init', methods=['GET'])
def google_init():
    """Initialize Google OAuth flow"""
    try:
        auth_url = oauth_service.get_google_auth_url()
        return jsonify({'authUrl': auth_url}), 200
    except Exception as e:
        current_app.logger.error(f"Google init error: {str(e)}")
        return jsonify({'error': 'Failed to initialize Google login'}), 500


@oauth_bp.route('/google/callback', methods=['POST'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        data = request.get_json()
        code = data.get('code')

        if not code:
            return jsonify({'error': 'Authorization code required'}), 400

        user_info = oauth_service.exchange_google_code(code)

        if not user_info:
            return jsonify({'error': 'Failed to authenticate with Google'}), 401

        # Check if user exists
        email = user_info.get('email')
        user = User.query.filter_by(email=email).first()

        if not user:
            # Create new user
            user = User()
            user.email = email
            user.password_hash = secrets.token_urlsafe(32)  # Random password
            user.is_admin = False
            db.session.add(user)  # type: ignore[attr-defined]
            db.session.commit()  # type: ignore[attr-defined]

        login_user(user)

        return jsonify({
            'message': 'Google login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Google callback error: {str(e)}")
        return jsonify({'error': 'Google authentication failed'}), 500


@oauth_bp.route('/whatsapp/init', methods=['POST'])
def whatsapp_init():
    """Initialize WhatsApp OAuth flow"""
    try:
        data = request.get_json()
        phone = data.get('phone')

        if not phone:
            return jsonify({'error': 'Phone number required'}), 400

        code = otp_service.create_challenge(phone)
        if not otp_service.send_otp_whatsapp(phone, code):
            return jsonify({'error': 'Failed to send WhatsApp code'}), 502
        return jsonify({'message': 'WhatsApp code sent', 'expires_in': 300}), 200

    except Exception as e:
        current_app.logger.error(f"WhatsApp init error: {str(e)}")
        return jsonify({'error': 'Failed to initialize WhatsApp login'}), 500


@oauth_bp.route('/whatsapp/callback', methods=['POST'])
def whatsapp_callback():
    """Handle WhatsApp OAuth callback"""
    try:
        data = request.get_json()
        code = data.get('code')
        phone = data.get('phone')

        if not code or not phone:
            return jsonify({'error': 'Authorization code and phone required'}), 400

        if not otp_service.verify_challenge(phone, code):
            return jsonify({'error': 'Invalid or expired WhatsApp code'}), 401

        # Check if user exists
        user = User.query.filter_by(phone_number=phone).first()

        if not user:
            user = User(
                email=f"{phone.lstrip('+').replace(' ', '')}@phone.phishguard.local",
                phone_number=phone,
                password_hash=secrets.token_urlsafe(32),
                is_admin=False,
                auth_provider='whatsapp',
            )
            db.session.add(user)  # type: ignore[attr-defined]
            db.session.commit()  # type: ignore[attr-defined]

        login_user(user)

        return jsonify({
            'message': 'WhatsApp login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"WhatsApp callback error: {str(e)}")
        return jsonify({'error': 'WhatsApp authentication failed'}), 500