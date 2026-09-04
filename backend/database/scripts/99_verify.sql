-- ============================================
-- PHISHGUARD-AI DATABASE VERIFICATION
-- ============================================

-- 1. Check all tables exist
SELECT 
    'Tables' AS check_type,
    COUNT(*) AS count
FROM information_schema.tables 
WHERE table_schema = 'public';

-- 2. Check column counts per table
SELECT 
    table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;

-- 3. Check data counts
SELECT 
    'users' AS table_name, 
    COUNT(*) AS row_count 
FROM users
UNION ALL
SELECT 'whitelist_domains', COUNT(*) FROM whitelist_domains
UNION ALL
SELECT 'suspicious_keywords', COUNT(*) FROM suspicious_keywords
UNION ALL
SELECT 'threat_categories', COUNT(*) FROM threat_categories
UNION ALL
SELECT 'analyses', COUNT(*) FROM analyses
UNION ALL
SELECT 'news_articles', COUNT(*) FROM news_articles
UNION ALL
SELECT 'mfa_sessions', COUNT(*) FROM mfa_sessions;

-- 4. Show sample whitelist domains
SELECT '=== SAMPLE WHITELIST ===' AS section;
SELECT domain, institution, category 
FROM whitelist_domains 
LIMIT 5;

-- 5. Show sample keywords
SELECT '=== SAMPLE KEYWORDS ===' AS section;
SELECT keyword, weight, language 
FROM suspicious_keywords 
LIMIT 5;

-- 6. Show threat categories
SELECT '=== THREAT CATEGORIES ===' AS section;
SELECT name, name_en, priority 
FROM threat_categories 
ORDER BY priority;

-- 7. Check foreign key relationships
SELECT '=== FOREIGN KEYS ===' AS section;
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS references_table
FROM pg_constraint
WHERE contype = 'f'
AND connamespace = 'public'::regnamespace;

-- 8. Check indexes
SELECT '=== INDEXES ===' AS section;
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;