-- ============================================
-- PHISHGUARD-AI: SOC platform upgrade
--   * user approval workflow + registration intelligence (IP, geo, device, risk)
--   * session version (real "sign out everywhere")
--   * security / audit events (login history, admin actions)
--   * incidents (auto-correlated campaigns) + domain blocklist
--   * allowlist logos + live domain health
--   * automatic report triage
-- Safe to run more than once. Run as the table owner (postgres).
-- ============================================

-- ---------- Users ----------
ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version          INTEGER      NOT NULL DEFAULT 1;
-- 'approved' | 'pending' (awaiting admin) | 'review' (further verification requested) | 'rejected'
ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_status          VARCHAR(20)  NOT NULL DEFAULT 'approved';
ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_note            TEXT         NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_by              INTEGER      NULL REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_at              TIMESTAMP    NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS region                   VARCHAR(60)  NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS city                     VARCHAR(120) NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title                VARCHAR(120) NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization             VARCHAR(160) NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at        TIMESTAMP    NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at      TIMESTAMP    NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_ip          VARCHAR(64)  NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_user_agent  VARCHAR(400) NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_geo         JSON         NULL;  -- country, city, isp, proxy, hosting…
ALTER TABLE users ADD COLUMN IF NOT EXISTS risk_score               INTEGER      NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS risk_flags               JSON         NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip            VARCHAR(64)  NULL;

CREATE INDEX IF NOT EXISTS idx_users_approval_status ON users(approval_status);
CREATE INDEX IF NOT EXISTS idx_users_registration_ip ON users(registration_ip);

-- ---------- Security & audit events ----------
CREATE TABLE IF NOT EXISTS security_events (
    id          SERIAL PRIMARY KEY,
    event_type  VARCHAR(40)  NOT NULL,      -- login_success, login_failed, admin_user_approved, …
    severity    VARCHAR(10)  NOT NULL DEFAULT 'info',   -- info | warning | critical
    user_id     INTEGER      NULL REFERENCES users(id) ON DELETE SET NULL,  -- account concerned
    actor_id    INTEGER      NULL REFERENCES users(id) ON DELETE SET NULL,  -- who did it (admin)
    ip          VARCHAR(64)  NULL,
    user_agent  VARCHAR(400) NULL,
    geo         JSON         NULL,
    details     JSON         NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_security_events_user    ON security_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_type    ON security_events(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_created ON security_events(created_at DESC);

-- ---------- Incidents (correlated campaigns) ----------
CREATE TABLE IF NOT EXISTS incidents (
    id              SERIAL PRIMARY KEY,
    ref             VARCHAR(30)  NOT NULL UNIQUE,         -- INC-2026-0001
    title           VARCHAR(255) NOT NULL,
    indicator       VARCHAR(255) NULL,                    -- correlation key (domain or brand)
    indicator_type  VARCHAR(20)  NULL,                    -- domain | brand | sender
    category        VARCHAR(60)  NULL,
    severity        VARCHAR(10)  NOT NULL DEFAULT 'medium',   -- critical | high | medium | low
    status          VARCHAR(20)  NOT NULL DEFAULT 'open',     -- open | investigating | contained | resolved | false_positive
    source          VARCHAR(10)  NOT NULL DEFAULT 'auto',     -- auto | manual
    analysis_ids    JSON         NOT NULL DEFAULT '[]',
    affected_users  INTEGER      NOT NULL DEFAULT 0,
    max_score       FLOAT        NOT NULL DEFAULT 0,
    assigned_to     INTEGER      NULL REFERENCES users(id) ON DELETE SET NULL,
    timeline        JSON         NOT NULL DEFAULT '[]',
    first_seen      TIMESTAMP    NULL,
    last_seen       TIMESTAMP    NULL,
    resolved_at     TIMESTAMP    NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_incidents_status    ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_indicator ON incidents(indicator);

-- ---------- Blocklist (fed by incidents / threat intel, used by the pipeline) ----------
CREATE TABLE IF NOT EXISTS blocked_domains (
    id           SERIAL PRIMARY KEY,
    domain       VARCHAR(255) NOT NULL UNIQUE,
    reason       TEXT         NULL,
    incident_id  INTEGER      NULL REFERENCES incidents(id) ON DELETE SET NULL,
    created_by   INTEGER      NULL REFERENCES users(id) ON DELETE SET NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ---------- Allowlist: logo + live health ----------
ALTER TABLE whitelist_domains ADD COLUMN IF NOT EXISTS logo_url        VARCHAR(500) NULL;
ALTER TABLE whitelist_domains ADD COLUMN IF NOT EXISTS website         VARCHAR(255) NULL;
ALTER TABLE whitelist_domains ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMP    NULL;
ALTER TABLE whitelist_domains ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMP    NULL;
ALTER TABLE whitelist_domains ADD COLUMN IF NOT EXISTS health          JSON         NULL;  -- dns, https, ssl_days_left, latency_ms

-- ---------- Automatic triage of the review queue ----------
-- review_source: 'admin' (human decision) | 'auto' (engine decision above the threshold)
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS review_source    VARCHAR(10) NULL;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS triage_label     VARCHAR(20) NULL;   -- engine suggestion
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS triage_confidence FLOAT      NULL;   -- 0-100
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS duration_ms      INTEGER     NULL;

CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);

-- The application account needs rights on the new tables
GRANT SELECT, INSERT, UPDATE, DELETE ON security_events, incidents, blocked_domains TO phishguard_user;
GRANT USAGE, SELECT ON SEQUENCE security_events_id_seq, incidents_id_seq, blocked_domains_id_seq TO phishguard_user;
