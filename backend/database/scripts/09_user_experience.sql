-- ============================================
-- PHISHGUARD-AI: mailbox scanner + user experience upgrade
--   * connected mailboxes (Gmail / Outlook OAuth, encrypted tokens)
--   * analyses: origin (web / mailbox / forward), "analyse first, sign in to see"
--     claim token, user feedback ("was this helpful?")
--   * users: onboarding + awareness quiz progress
--   * allowlist: official support contact shown in "what to do"
-- Safe to run more than once. Run as the table owner (postgres) on phishguard_db.
-- ============================================

-- ---------- Connected mailboxes ----------
CREATE TABLE IF NOT EXISTS mailbox_connections (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider          VARCHAR(20)  NOT NULL,              -- 'gmail' | 'outlook'
    email             VARCHAR(255) NOT NULL,
    access_token_enc  TEXT         NULL,                  -- encrypted (app/services/crypto_box.py)
    refresh_token_enc TEXT         NULL,
    token_expires_at  TIMESTAMP    NULL,
    scopes            TEXT         NULL,
    status            VARCHAR(20)  NOT NULL DEFAULT 'active',  -- active | paused | error | revoked
    sync_cursor       TEXT         NULL,                  -- Gmail historyId / Graph deltaLink
    last_sync_at      TIMESTAMP    NULL,
    last_error        TEXT         NULL,
    scanned_count     INTEGER      NOT NULL DEFAULT 0,
    threat_count      INTEGER      NOT NULL DEFAULT 0,
    auto_label        BOOLEAN      NOT NULL DEFAULT FALSE,  -- add a "PhishGuard" label/category to threats
    created_at        TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, provider, email)
);

-- ---------- Analyses ----------
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS source            VARCHAR(20)  NOT NULL DEFAULT 'web';  -- web | mailbox | forward | share
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS mailbox_id        INTEGER      NULL REFERENCES mailbox_connections(id) ON DELETE SET NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS external_id       VARCHAR(255) NULL;  -- provider message id (dedupe)
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS claim_token_hash  VARCHAR(64)  NULL;  -- visitor scan, result shown after sign-in
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS claim_expires_at  TIMESTAMP    NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS claimed_at        TIMESTAMP    NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS feedback          SMALLINT     NULL;  -- 1 helpful, -1 not helpful
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS feedback_note     TEXT         NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS feedback_at       TIMESTAMP    NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_analyses_mailbox_message ON analyses (mailbox_id, external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_analyses_claim_token ON analyses (claim_token_hash) WHERE claim_token_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_analyses_source ON analyses (source);

-- ---------- Users ----------
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarded_at   TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_xp        INTEGER   NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_answered  INTEGER   NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_correct   INTEGER   NOT NULL DEFAULT 0;

-- ---------- Allowlist ----------
ALTER TABLE whitelist_domains ADD COLUMN IF NOT EXISTS support_contact VARCHAR(160) NULL;  -- e.g. official hotline, set by an admin

GRANT SELECT, INSERT, UPDATE, DELETE ON mailbox_connections TO phishguard_user;
GRANT USAGE, SELECT ON SEQUENCE mailbox_connections_id_seq TO phishguard_user;
