"""
OTP Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user
from app import db
from app.models import User
from app.services.otp_service import OTPService
import secrets

otp_bp = Blueprint('otp', __name__)
otp_service = OTPService()


@otp_bp.route('/send', methods=['POST'])
def send_otp():
    """Send OTP to phone number"""
    try:
        data = request.get_json()
        phone = data.get('phone')

        if not phone:
            return jsonify({'error': 'Phone number required'}), 400

        # Generate OTP
        otp = otp_service.create_challenge(phone)

        # Send OTP via SMS
        sent = otp_service.send_otp_sms(phone, otp)

        if not sent:
            return jsonify({'error': 'Failed to send OTP'}), 500

        return jsonify({
            'message': 'OTP sent successfully',
            'expires_in': 300  # 5 minutes
        }), 200

    except Exception as e:
        current_app.logger.error(f"Send OTP error: {str(e)}")
        return jsonify({'error': 'Failed to send OTP'}), 500


@otp_bp.route('/verify', methods=['POST'])
def verify_otp():
    """Verify OTP code"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        code = data.get('code')

        if not phone or not code:
            return jsonify({'error': 'Phone and code required'}), 400

        # Verify OTP
        if not otp_service.verify_challenge(phone, code):
            return jsonify({'error': 'Invalid or expired OTP'}), 400

        # Check if user exists
        user = User.query.filter_by(phone_number=phone).first()
        if not user:
            user = User(
                email=f"{phone.lstrip('+').replace(' ', '')}@phone.phishguard.local",
                phone_number=phone,
                password_hash=secrets.token_urlsafe(32),
                auth_provider='phone',
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)

        return jsonify({
            'message': 'OTP verified successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Verify OTP error: {str(e)}")
        return jsonify({'error': 'OTP verification failed'}), 500


@otp_bp.route('/resend', methods=['POST'])
def resend_otp():
    """Resend OTP"""
    try:
        data = request.get_json()
        phone = data.get('phone')

        if not phone:
            return jsonify({'error': 'Phone number required'}), 400

        # Generate new OTP
        otp = otp_service.create_challenge(phone)

        sent = otp_service.send_otp_sms(phone, otp)

        if not sent:
            return jsonify({'error': 'Failed to resend OTP'}), 500

        return jsonify({
            'message': 'OTP resent successfully',
            'expires_in': 300
        }), 200

    except Exception as e:
        current_app.logger.error(f"Resend OTP error: {str(e)}")
        return jsonify({'error': 'Failed to resend OTP'}), 500