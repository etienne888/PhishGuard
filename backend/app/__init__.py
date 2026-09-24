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

    @app.after_request
    def add_request_metadata(response):
        duration_ms = round((perf_counter() - g.request_started_at) * 1000)
        response.headers['X-Request-ID'] = g.request_id

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
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

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
    
    return app