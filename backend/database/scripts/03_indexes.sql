-- ============================================
-- PHISHGUARD-AI PERFORMANCE INDEXES
-- Version: 1.0
-- Date: 2026-09-03
-- Description: Indexes for query performance
-- ============================================

-- Analyses table indexes
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_score_risk ON analyses(score_risk);
CREATE INDEX IF NOT EXISTS idx_analyses_verdict ON analyses(verdict);

-- Whitelist indexes
CREATE INDEX IF NOT EXISTS idx_whitelist_domains_domain ON whitelist_domains(domain);
CREATE INDEX IF NOT EXISTS idx_whitelist_domains_category ON whitelist_domains(category);

-- Suspicious keywords indexes
CREATE INDEX IF NOT EXISTS idx_suspicious_keywords_language ON suspicious_keywords(language);

-- News articles indexes
CREATE INDEX IF NOT EXISTS idx_news_articles_published_date ON news_articles(published_date);
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles(source);

-- MFA sessions indexes
CREATE INDEX IF NOT EXISTS idx_mfa_sessions_expires_at ON mfa_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_mfa_sessions_user_id ON mfa_sessions(user_id);

-- Show all indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;