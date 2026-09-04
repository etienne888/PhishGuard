# backend/app/api/__init__.py

from app.api.routes import api_bp
from app.api.auth import auth_bp
from app.api.mobilemoney import mobile_money_bp
from app.api.oauth import oauth_bp
from app.api.otp import otp_bp
from app.api.verification import verification_bp