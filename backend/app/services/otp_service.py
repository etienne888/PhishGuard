import logging
import os
from requests.auth import HTTPBasicAuth
import requests

from app.services.verification_service import VerificationService

logger = logging.getLogger(__name__)


class OTPService:
    """Generate OTPs and provide a development-safe delivery hook."""

    def generate_otp(self) -> str:
        return VerificationService().generate_code()

    def create_challenge(self, phone: str) -> str:
        return VerificationService().create_challenge(phone, 'phone')

    def verify_challenge(self, phone: str, code: str) -> bool:
        return VerificationService().verify_challenge(phone, 'phone', code)

    def send_otp_sms(self, phone: str, code: str) -> bool:
        sid = os.getenv('TWILIO_ACCOUNT_SID')
        token = os.getenv('TWILIO_AUTH_TOKEN')
        sender = os.getenv('TWILIO_SMS_FROM')
        if sid and token and sender:
            response = requests.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',
                data={'To': phone, 'From': sender, 'Body': f'PhishGuard-AI code: {code}'},
                auth=HTTPBasicAuth(sid, token),
                timeout=10,
            )
            return response.ok
        logger.info("Development OTP for %s: %s", phone, code)
        return True

    def send_otp_whatsapp(self, phone: str, code: str) -> bool:
        sid = os.getenv('TWILIO_ACCOUNT_SID')
        token = os.getenv('TWILIO_AUTH_TOKEN')
        sender = os.getenv('TWILIO_WHATSAPP_FROM')
        if sid and token and sender:
            response = requests.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',
                data={'To': f'whatsapp:{phone}', 'From': f'whatsapp:{sender}', 'Body': f'PhishGuard-AI code: {code}'},
                auth=HTTPBasicAuth(sid, token),
                timeout=10,
            )
            return response.ok
        logger.info("Development WhatsApp OTP for %s: %s", phone, code)
        return True
