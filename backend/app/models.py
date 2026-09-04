# backend/app/models.py

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(30), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    auth_provider = db.Column(db.String(30), default='password', nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32), nullable=True)
    mfa_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    
    def get_id(self):
        return str(self.id)

class Analysis(db.Model):
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    text_source = db.Column(db.Text, nullable=False)
    score_risk = db.Column(db.Float, nullable=False)
    verdict = db.Column(db.String(50), nullable=False)
    indicators = db.Column(db.JSON, nullable=False)
    email_from = db.Column(db.String(255), nullable=True)
    subject = db.Column(db.String(255), nullable=True)
    urls = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WhitelistDomain(db.Model):
    __tablename__ = 'whitelist_domains'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    institution = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SuspiciousKeyword(db.Model):
    __tablename__ = 'suspicious_keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(255), unique=True, nullable=False)
    weight = db.Column(db.Integer, default=10)
    language = db.Column(db.String(10), default='fr')

class ThreatCategory(db.Model):
    __tablename__ = 'threat_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    name_en = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text, nullable=True)
    mechanism = db.Column(db.Text, nullable=False)
    mechanism_en = db.Column(db.Text, nullable=True)
    warning_signs = db.Column(db.Text, nullable=False)
    warning_signs_en = db.Column(db.Text, nullable=True)
    action_to_take = db.Column(db.Text, nullable=False)
    action_to_take_en = db.Column(db.Text, nullable=True)
    how_to_report = db.Column(db.Text, nullable=False)
    how_to_report_en = db.Column(db.Text, nullable=True)
    keywords_fr = db.Column(db.JSON, nullable=True)
    keywords_en = db.Column(db.JSON, nullable=True)

class NewsArticle(db.Model):
    __tablename__ = 'news_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('threat_categories.id'), nullable=True)
    published_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('ThreatCategory', backref='articles')

class MFASession(db.Model):
    __tablename__ = 'mfa_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    temp_token = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='mfa_sessions')


class OAuthAccount(db.Model):
    __tablename__ = 'oauth_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(30), nullable=False)
    provider_subject = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='oauth_accounts')
    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_subject', name='uq_oauth_provider_subject'),
    )


class VerificationChallenge(db.Model):
    __tablename__ = 'verification_challenges'

    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(20), nullable=False)
    code_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    consumed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)