"""
Verification Routes (Email Code)
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user
from app import db
from app.models import User
from app.services.verification_service import VerificationService

verification_bp = Blueprint('verification', __name__)
verification_service = VerificationService()


@verification_bp.route('/send-email-code', methods=['POST'])
def send_email_code():
    """Send verification code to email"""
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email required'}), 400

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Generate verification code
        code = verification_service.create_challenge(email, 'email')

        # Send email
        sent = verification_service.send_verification_email(email, code)

        if not sent:
            return jsonify({'error': 'Failed to send verification email'}), 500

        return jsonify({
            'message': 'Verification code sent successfully',
            'expires_in': 300
        }), 200

    except Exception as e:
        current_app.logger.error(f"Send email code error: {str(e)}")
        return jsonify({'error': 'Failed to send verification code'}), 500


@verification_bp.route('/verify-email-code', methods=['POST'])
def verify_email_code():
    """Verify email code"""
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')

        if not email or not code:
            return jsonify({'error': 'Email and code required'}), 400

        if not verification_service.verify_challenge(email, 'email', code):
            return jsonify({'error': 'Invalid or expired verification code'}), 400

        # Get user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.email_verified = True
        db.session.commit()

        login_user(user)

        return jsonify({
            'message': 'Email verified successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Verify email code error: {str(e)}")
        return jsonify({'error': 'Verification failed'}), 500


@verification_bp.route('/resend-email-code', methods=['POST'])
def resend_email_code():
    """Resend email verification code"""
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email required'}), 400

        # Generate new code
        code = verification_service.create_challenge(email, 'email')

        sent = verification_service.send_verification_email(email, code)

        if not sent:
            return jsonify({'error': 'Failed to resend verification code'}), 500

        return jsonify({
            'message': 'Verification code resent successfully',
            'expires_in': 300
        }), 200

    except Exception as e:
        current_app.logger.error(f"Resend email code error: {str(e)}")
        return jsonify({'error': 'Failed to resend verification code'}), 500