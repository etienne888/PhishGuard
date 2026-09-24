-- ============================================
-- PHISHGUARD-AI: review queue (user reports + admin decisions)
-- Adds report / review tracking to analyses. Safe to run more than once.
-- ============================================

ALTER TABLE analyses ADD COLUMN IF NOT EXISTS reported_at   TIMESTAMP NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS report_note   TEXT NULL;
-- NULL = never reviewed | 'phishing' | 'safe'  (admin ground truth, reused for retraining)
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS review_label  VARCHAR(20) NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS reviewed_by   INTEGER NULL REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS reviewed_at   TIMESTAMP NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS review_note   TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_analyses_reported_at  ON analyses(reported_at);
CREATE INDEX IF NOT EXISTS idx_analyses_review_label ON analyses(review_label);

-- Old /api/v2 test rows stored the 4-level risk instead of the dashboard verdict
UPDATE analyses SET verdict = 'phishing'   WHERE verdict IN ('Critical', 'High');
UPDATE analyses SET verdict = 'suspicious' WHERE verdict = 'Medium';
UPDATE analyses SET verdict = 'legitimate' WHERE verdict = 'Low';
