-- ============================================
-- PHISHGUARD-AI DATABASE SCHEMA
-- RUN THIS FIRST - ALL TABLES
-- ============================================

-- 1. USERS TABLE
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(32) NULL,
    mfa_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL
);

-- 2. ANALYSES TABLE
CREATE TABLE analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    text_source TEXT NOT NULL,
    score_risk FLOAT NOT NULL,
    verdict VARCHAR(50) NOT NULL,
    indicators JSONB NOT NULL,
    email_from VARCHAR(255) NULL,
    subject VARCHAR(255) NULL,
    urls JSONB NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. WHITELIST DOMAINS
CREATE TABLE whitelist_domains (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    institution VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. SUSPICIOUS KEYWORDS
CREATE TABLE suspicious_keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) UNIQUE NOT NULL,
    weight INTEGER DEFAULT 10,
    language VARCHAR(10) DEFAULT 'fr'
);

-- 5. THREAT CATEGORIES
CREATE TABLE threat_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    name_en VARCHAR(255) NULL,
    priority INTEGER NOT NULL,
    description TEXT NOT NULL,
    description_en TEXT NULL,
    mechanism TEXT NOT NULL,
    mechanism_en TEXT NULL,
    warning_signs TEXT NOT NULL,
    warning_signs_en TEXT NULL,
    action_to_take TEXT NOT NULL,
    action_to_take_en TEXT NULL,
    how_to_report TEXT NOT NULL,
    how_to_report_en TEXT NULL,
    keywords_fr JSONB NULL,
    keywords_en JSONB NULL
);

-- 6. NEWS ARTICLES
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,
    summary TEXT NULL,
    category_id INTEGER REFERENCES threat_categories(id) ON DELETE SET NULL,
    published_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. MFA SESSIONS
CREATE TABLE mfa_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    temp_token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);