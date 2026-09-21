-- Dynamic user dashboard support.

ALTER TABLE analyses ADD COLUMN IF NOT EXISTS reported_at TIMESTAMP NULL;

CREATE INDEX IF NOT EXISTS ix_analyses_user_created_at
    ON analyses (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_analyses_user_verdict_created_at
    ON analyses (user_id, verdict, created_at DESC);