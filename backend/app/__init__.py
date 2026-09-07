import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager

load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
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
    CORS(
        app,
        origins=os.getenv(
            'CORS_ORIGINS',
            'http://localhost:5173,http://localhost:5174,http://localhost:5177,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5177'
        ).split(','),
        supports_credentials=True,
    )
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.api.routes import api_bp
    from app.api.auth import auth_bp
    from app.api.mobilemoney import mobile_money_bp
    from app.api.oauth import oauth_bp
    from app.api.otp import otp_bp
    from app.api.verification import verification_bp
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(mobile_money_bp, url_prefix='/api/mobile-money')
    app.register_blueprint(oauth_bp, url_prefix='/api/oauth')
    app.register_blueprint(otp_bp, url_prefix='/api/otp')
    app.register_blueprint(verification_bp, url_prefix='/api/verification')
    
    return app