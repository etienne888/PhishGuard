-- ============================================
-- PHISHGUARD-AI SEED DATA (FULLY FIXED)
-- Version: 1.3
-- Date: 2026-09-03
-- Description: Seed data with proper JSONB casting
-- ============================================

-- ============================================
-- WHITELIST: Camerounian Institutions
-- ============================================

INSERT INTO whitelist_domains (domain, institution, category)
SELECT * FROM (VALUES
    ('mtn.cm', 'MTN Cameroon', 'mobile_money'),
    ('orange.cm', 'Orange Cameroon', 'mobile_money'),
    ('camtel.cm', 'CAMTEL', 'telecom'),
    ('afrilandfirstbank.com', 'Afriland First Bank', 'banking'),
    ('ubacameroon.com', 'UBA Cameroon', 'banking'),
    ('sgc.cm', 'Société Générale Cameroun', 'banking'),
    ('ecobank.cm', 'Ecobank Cameroun', 'banking'),
    ('biccm.cm', 'BICEC', 'banking'),
    ('antic.cm', 'ANTIC', 'government'),
    ('cirt.cm', 'CIRT-CM', 'government'),
    ('cnps.cm', 'CNPS', 'government'),
    ('minpostel.gov.cm', 'MINPOSTEL', 'government')
) AS v(domain, institution, category)
WHERE NOT EXISTS (SELECT 1 FROM whitelist_domains WHERE domain = v.domain);

-- ============================================
-- SUSPICIOUS KEYWORDS
-- ============================================

INSERT INTO suspicious_keywords (keyword, weight, language)
SELECT * FROM (VALUES
    -- French
    ('urgent', 20, 'fr'),
    ('immediat', 20, 'fr'),
    ('bloqué', 25, 'fr'),
    ('suspendu', 25, 'fr'),
    ('code pin', 30, 'fr'),
    ('mot de passe', 30, 'fr'),
    ('vérifier', 15, 'fr'),
    ('cliquez ici', 20, 'fr'),
    ('confirmer', 15, 'fr'),
    ('compte désactivé', 25, 'fr'),
    -- English
    ('account blocked', 25, 'en'),
    ('verify now', 20, 'en'),
    ('urgent action', 25, 'en'),
    ('password reset', 20, 'en'),
    ('click here', 20, 'en'),
    ('suspended', 20, 'en')
) AS v(keyword, weight, language)
WHERE NOT EXISTS (SELECT 1 FROM suspicious_keywords WHERE keyword = v.keyword);

-- ============================================
-- THREAT CATEGORIES
-- ============================================

INSERT INTO threat_categories (name, name_en, priority, description, mechanism, warning_signs, action_to_take, how_to_report, keywords_fr, keywords_en)
SELECT * FROM (VALUES
    (
        'Phishing / Hameçonnage',
        'Phishing',
        1,
        'Tentative de fraude par email, SMS ou appel pour obtenir vos informations personnelles',
        'L''attaquant se fait passer pour une institution légitime (banque, opérateur mobile, administration) et vous envoie un message contenant un lien vers un faux site de connexion.',
        'Urgence artificielle, fautes d''orthographe, lien suspect, demande de données personnelles.',
        'Ne cliquez jamais sur les liens. Vérifiez toujours via le canal officiel. Signalez le message.',
        'CIRT-CM: 8202 ou alerts@cirt.cm',
        '["phishing","hameçonnage","arnaque","email","sms","cliquez"]'::jsonb,  -- ✅ CAST
        '["phishing","scam","email","sms","click"]'::jsonb                       -- ✅ CAST
    ),
    (
        'Fraude Mobile Money (faux agent)',
        'Mobile Money Fraud',
        2,
        'Escroquerie par téléphone ou SMS où l''attaquant se fait passer pour un agent MTN/Orange',
        'L''attaquant appelle en se présentant comme agent officiel et demande votre code PIN ou vous invite à effectuer une opération frauduleuse.',
        'Demande de PIN/OTP par téléphone, ton pressant, numéro non officiel.',
        'Ne jamais communiquer votre PIN. Raccrochez et rappelez le numéro officiel de l''opérateur.',
        'CIRT-CM: 8202 ou alerts@cirt.cm',
        '["mobile money","mtn","orange","agent","pin","code"]'::jsonb,           -- ✅ CAST
        '["mobile money","mtn","orange","agent","pin","code"]'::jsonb            -- ✅ CAST
    ),
    (
        'Ingénierie sociale',
        'Social Engineering',
        3,
        'Manipulation psychologique pour obtenir des informations confidentielles',
        'L''attaquant exploite la confiance, la peur ou l''urgence pour vous faire agir contre votre intérêt.',
        'Appel à l''émotion, urgence familiale, demande d''argent pressante.',
        'Toujours vérifier par un second canal avant d''agir, même en situation d''urgence.',
        'CIRT-CM: 8202 ou alerts@cirt.cm',
        '["ingénierie sociale","manipulation","urgence","famille"]'::jsonb,      -- ✅ CAST
        '["social engineering","manipulation","urgency","family"]'::jsonb         -- ✅ CAST
    )
) AS v(name, name_en, priority, description, mechanism, warning_signs, action_to_take, how_to_report, keywords_fr, keywords_en)
WHERE NOT EXISTS (SELECT 1 FROM threat_categories WHERE name = v.name);

-- ============================================
-- VERIFICATION
-- ============================================

SELECT '✅ Seed data inserted successfully!' AS status;

SELECT 
    (SELECT COUNT(*) FROM whitelist_domains) AS whitelist_count,
    (SELECT COUNT(*) FROM suspicious_keywords) AS keyword_count,
    (SELECT COUNT(*) FROM threat_categories) AS threat_count;

-- Show what was inserted
SELECT '===== WHITELIST DOMAINS =====' AS section;
SELECT domain, institution, category FROM whitelist_domains ORDER BY institution;

SELECT '===== SUSPICIOUS KEYWORDS =====' AS section;
SELECT keyword, weight, language FROM suspicious_keywords ORDER BY language, keyword;

SELECT '===== THREAT CATEGORIES =====' AS section;
SELECT name, name_en, priority, keywords_fr FROM threat_categories ORDER BY priority;