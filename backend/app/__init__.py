import os
import logging
from time import perf_counter
from uuid import uuid4
from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager

load_dotenv()

# Surface dev-mode OTP/verification codes (logged instead of emailed when SMTP isn't configured)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['APP_STARTED_AT'] = perf_counter()
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://phishguard_user:phishguard123@localhost:5432/phishguard_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    configured_origins = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,http://localhost:5174,http://localhost:5177,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5177'
    ).split(',')
    frontend_url = os.getenv('FRONTEND_URL', '').rstrip('/')
    if frontend_url and frontend_url not in configured_origins:
        configured_origins.append(frontend_url)
    CORS(app, origins=configured_origins, supports_credentials=True)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @app.before_request
    def begin_request_timing():
        g.request_id = str(uuid4())
        g.request_started_at = perf_counter()

    @app.before_request
    def start_background_jobs():
        # First request served: start mailbox sync, forwarded emails, correlation… (services/scheduler.py)
        from app.services import scheduler
        scheduler.start(app)

    @app.before_request
    def enforce_idle_timeout():
        # Sign out sessions idle for longer than the platform policy (Settings › Sessions)
        from datetime import datetime
        from flask import session
        from flask_login import current_user, logout_user
        if not request.path.startswith('/api/') or not current_user.is_authenticated:
            return None
        from app.services import settings_service
        now = datetime.utcnow().timestamp()
        timeout = (settings_service.get('session_timeout_min') or 0) * 60
        last_seen = session.get('last_seen')
        if timeout and last_seen and now - last_seen > timeout:
            logout_user()
            session.clear()
            return jsonify({'error': {'code': 'SESSION_EXPIRED', 'message': 'Session expired after inactivity.', 'detail': None}}), 401
        session['last_seen'] = now
        return None

    @app.after_request
    def add_request_metadata(response):
        duration_ms = round((perf_counter() - g.request_started_at) * 1000)
        response.headers['X-Request-ID'] = g.request_id
        if request.path.startswith('/api/'):
            from app.services.system_metrics import record_request
            record_request(request.method, request.url_rule.rule if request.url_rule else request.path,
                           response.status_code, duration_ms)

        if duration_ms > 500:
            app.logger.warning(
                'Slow request %s %s completed in %sms',
                request.method,
                request.path,
                duration_ms,
            )

        if not request.path.startswith('/api/') or response.status_code == 204 or not response.is_json:
            return response

        payload = response.get_json()
        if isinstance(payload, dict) and ('data' in payload or 'error' in payload):
            if 'data' in payload and 'meta' not in payload:
                payload = {
                    'data': payload['data'],
                    'meta': {'request_id': g.request_id, 'duration_ms': duration_ms},
                }
            elif 'error' in payload and not isinstance(payload['error'], dict):
                payload = {
                    'error': {
                        'code': 'REQUEST_FAILED',
                        'message': str(payload['error']),
                        'detail': None,
                    }
                }
            elif 'error' in payload:
                payload['error'].setdefault('code', 'REQUEST_FAILED')
                payload['error'].setdefault('detail', None)
            else:
                payload['meta'].update({'request_id': g.request_id, 'duration_ms': duration_ms})
        else:
            payload = {
                'data': payload,
                'meta': {'request_id': g.request_id, 'duration_ms': duration_ms},
            }

        normalized = jsonify(payload)
        normalized.status_code = response.status_code
        normalized.headers['X-Request-ID'] = g.request_id
        return normalized
    
    # Register blueprints
    from app.api.routes import api_bp
    from app.api.auth import auth_bp
    from app.api.admin import admin_bp
    from app.api.mobilemoney import mobile_money_bp
    from app.api.oauth import oauth_bp
    from app.api.otp import otp_bp
    from app.api.user_dashboard import user_dashboard_bp
    from app.api.verification import verification_bp
    from app.api.scan import scan_bp
    from app.api.user_profile import user_profile_bp
    from app.api.admin_ops import admin_ops_bp
    from app.api.admin_security import admin_security_bp
    from app.api.admin_soc import admin_soc_bp
    from app.api.mailbox import mailbox_bp
    from app.api.admin_geo import admin_geo_bp
    from app.api.public import public_bp
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        # Session ids look like "42:3" (user id : session version). A bumped
        # version, a suspended account or one awaiting approval ends the session.
        raw_id, _, version = str(user_id).partition(':')
        try:
            user = db.session.get(User, int(raw_id))
        except (TypeError, ValueError):
            return None
        if user is None or (version and int(version) != (user.session_version or 1)):
            return None
        if user.status == 'suspended' or (user.approval_status or 'approved') != 'approved':
            return None
        return user

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({
                'error': {
                    'code': 'AUTH_REQUIRED',
                    'message': 'Authentication required.',
                    'detail': None,
                }
            }), 401
        return login_manager.login_url(login_manager.login_view)
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(mobile_money_bp, url_prefix='/api/mobile-money')
    app.register_blueprint(oauth_bp, url_prefix='/api/oauth')
    app.register_blueprint(otp_bp, url_prefix='/api/otp')
    app.register_blueprint(user_dashboard_bp, url_prefix='/api/user')
    app.register_blueprint(verification_bp, url_prefix='/api/verification')
    app.register_blueprint(scan_bp, url_prefix='/api/v2')
    app.register_blueprint(user_profile_bp, url_prefix='/api/user')
    app.register_blueprint(admin_ops_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_security_bp, url_prefix='/api/admin/security')
    app.register_blueprint(admin_soc_bp, url_prefix='/api/admin')
    app.register_blueprint(mailbox_bp, url_prefix='/api/mailbox')
    app.register_blueprint(admin_geo_bp, url_prefix='/api/admin')
    app.register_blueprint(public_bp, url_prefix='/api/public')
    
    return app