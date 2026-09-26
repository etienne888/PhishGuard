# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

PhishGuard-AI is a phishing detection and cybersecurity awareness platform for Cameroon. It has a Flask/PostgreSQL backend (`backend/`) and a Vue 3 + TypeScript frontend (`frontend/PhishGuard-AI/`).

## Commands

### Backend (`backend/`)

```bash
# Activate the venv first (Windows)
backend\venv\Scripts\activate

pip install -r requirements.txt      # full install (with ML deps: scikit-learn, pandas, nltk)
pip install -r requirements_no_ml.txt  # without ML deps
pip install -r requirements_pure.txt

python run.py                        # run dev server at http://localhost:5000

pytest                               # run tests (e.g. app/ml_engine/test_url_features.py)
pytest app/ml_engine/test_url_features.py -v   # single test file

python train_ml.py                   # retrain the Naive Bayes text classifier (writes app/ml_engine/trained/classifier.joblib)
python check_database.py             # sanity-check DB connectivity/schema
```

Database schema/seed SQL lives in `backend/database/scripts/`, applied in numeric order (`01_schema.sql` … `06_admin_platform.sql`, `99_verify.sql` to verify). There is no Alembic/Flask-Migrate migration history checked in yet, even though `Flask-Migrate` is wired up in `app/__init__.py` — schema changes are currently made by editing/adding numbered SQL scripts and `app/models.py` together.

Copy `backend/.env.example` to `backend/.env` and fill in `DATABASE_URL`, `SECRET_KEY`, and (optionally) Google OAuth / SMTP / Twilio credentials. Without SMTP/Twilio configured, OTP and verification codes are logged instead of sent (see logging setup in `app/__init__.py`).

### Frontend (`frontend/PhishGuard-AI/`)

```bash
npm install
npm run dev          # Vite dev server on :5173, proxies /api -> http://127.0.0.1:5000
npm run build         # type-check (vue-tsc) + vite build
npm run type-check    # vue-tsc --build only
npm run preview
```

## Architecture

### Backend request/response shape

`app/__init__.py` (`create_app`) wraps **every** `/api/*` JSON response in an `after_request` hook that normalizes payloads to:
- `{"data": ..., "meta": {"request_id", "duration_ms"}}` on success
- `{"error": {"code", "message", "detail"}}` on failure

Route handlers should return plain dicts under `data`/`error` keys (or bare payloads, which get auto-wrapped) — do not hand-roll the envelope in each handler. The frontend's `apiFetch` (`src/services/http.ts`) unwraps this envelope and throws `ApiError` on non-2xx responses or malformed JSON.

Blueprints are registered under fixed prefixes in `create_app()`:
- `app/api/routes.py` → `/api` (core analysis endpoints)
- `app/api/auth.py` → `/api/auth`
- `app/api/admin.py` → `/api/admin`
- `app/api/mobilemoney.py` → `/api/mobile-money`
- `app/api/oauth.py` → `/api/oauth`
- `app/api/otp.py` → `/api/otp`
- `app/api/user_dashboard.py` → `/api/user`
- `app/api/verification.py` → `/api/verification`

Auth uses Flask-Login session cookies (not JWT) — `login_manager.unauthorized_handler` returns a JSON 401 for `/api/*` paths and a redirect otherwise. Cross-cutting concerns (request ID, request timing, slow-request logging) are also handled in the `before_request`/`after_request` hooks in `app/__init__.py` rather than per-route.

### ML/detection engine (`backend/app/ml_engine/`)

`hybrid_detector.py`'s `HybridDetector.analyze(text, sender_domain)` is the single entry point used by the API layer. It fuses three signals into one score/verdict:
1. **Text model** — `model_manager.NaiveBayesClassifier`, loaded from `trained/classifier.joblib` (trained via `train_ml.py`).
2. **URL model** — `url_model.URLClassifier`, loaded from `trained/url_model.pkl` (trained via `train_url.py`); applied to every URL extracted by `url_features.extract_urls_from_text`.
3. **Heuristic scorer** — `heuristic_scorer.HeuristicScorer` (keyword/domain heuristics, French-language phishing cues).

Both trained models are optional at load time (missing files are caught and logged, not fatal) — when the URL model is absent, its 45% weight is redistributed to the text model (60%) and heuristics (40%). Verdict thresholds: `>80` Critical, `>60` High, `>40` Medium, else Low. When touching scoring weights/thresholds, update both branches of the weighted-fusion `if` in `analyze()` together, and note this logic is intentionally "backward compatible" — the return dict's core keys (`score`, `verdict`, `ml_score`, `heuristic_score`, `indicators`) must stay stable; `url_score`/`url_verdict` are additive-only.

Indicator strings surfaced to the UI are French-language phishing cues (urgency, credential requests, mobile-money context) — see `_get_indicators`.

### SOC platform (admin security operations)

Database: `database/scripts/08_soc_platform.sql` (run as `postgres`, the table owner). Backend services in `app/services/`, each with one job:

- `client_info.py` — real client IP (trusts `X-Forwarded-For` only from a local proxy), device label, IP geolocation (ip-api.com: country, ISP, `proxy`/`hosting` flags).
- `audit_service.record()` — every login, security change and admin action goes to `security_events`; login history and the audit log are views of that table. Never raises.
- `registration_risk.py` — sign-up risk score (disposable email, IP reuse, VPN/datacentre, honeypot field, fill time…) + approval decision from `registration_mode`.
- `triage_service.py` — engine suggestion + confidence for review-queue items; `triage_mode` manual/assisted/auto, `triage_threshold` (default 80). Auto decisions use `review_source='auto'` and are excluded from the retraining export.
- `indicators.py` → `correlation_service.py` — IOC extraction and incident correlation (N dangerous messages sharing a domain/brand in a window → incident with a JSON timeline); `blocked_domains` feeds the pipeline (`url_intel` forces blocklisted links to 85+).
- `system_metrics.py` (request ring buffer filled in `after_request`, psutil, DB stats), `domain_health.py` (allowlist DNS/TLS checks), `threat_feed.py` (OpenPhish, cached in `instance/`).

Security model: session ids are `"<user id>:<session_version>"` (`User.get_id`, `load_user` in `app/__init__.py`) — bumping `session_version` signs a user out everywhere; `load_user` also refuses suspended or unapproved accounts. Sensitive admin endpoints use `@sudo_required` (`app/api/security.py`): the frontend's `apiFetch` catches `SUDO_REQUIRED`, shows `SudoModal` and replays the request. Idle sessions expire after `session_timeout_min`.

APIs: `admin_security.py` (`/api/admin/security/*`: posture, sudo, sessions, events/audit), `admin_soc.py` (`/api/admin`: system, incidents, intel, blocklist), `admin.py` (users + approval workflow), `admin_ops.py` (review queue + triage, allowlist + health). Frontend: `services/soc.service.ts`, shared admin UI kit in `components/admin/ui/` (PageHeader, Panel, StatTile, Pill, Sparkline, RingGauge).

### Mailbox scanner and user experience

Database: `database/scripts/09_user_experience.sql`. Services in `app/services/`:

- `scan_service.py` — one place to store a pipeline result (web, mailbox, forward, share) and run SOC automation. **Visitors**: `/api/v2/scan` analyses but returns only `{gated, claim_token}`; the result is revealed by `POST /api/v2/scan/claim` after sign-in (token hash stored, single use, 24 h). Never return verdicts to anonymous callers (legacy `/api/analyze` requires login too).
- `mailbox_service.py` — Gmail / Outlook OAuth (read-only by default), token refresh, sync by received-date cursor, dedupe on `(mailbox_id, external_id)`; safe emails keep only their subject. Tokens encrypted with `crypto_box.py` (Fernet if `cryptography` is installed, else an HMAC-SHA256 stdlib construction).
- `inbound_service.py` — "forward to PhishGuard" inbox polled over IMAP; members get the verdict by email, unknown senders a claim link.
- `scheduler.py` — daemon thread started on the first request: mailbox sync, forwarded emails, correlation, OpenPhish, allowlist health; status shown on the admin System page.

APIs: `api/mailbox.py` (`/api/mailbox`), `api/public.py` (`/api/public/alerts`, anonymised incidents), plus `/api/user/summary`, `/quiz/answer`, `/onboarded`, `DELETE /api/user/analyses[/<id>]`. Frontend: `components/check/*` (composer with OCR via lazy `tesseract.js`, live steps, gate, result card with highlights/what-to-do/read-aloud/feedback), views `/check` (also the PWA share target), `/learn`, `/privacy`, `/dashboard/mailboxes`; PWA files in `public/` (`manifest.webmanifest`, `sw.js`, never caches `/api`). Icons: `components/ui/AppIcon.vue` + `icons.ts`. Strings: `i18n/locales/{fr,en}/ux.ts`.

### Frontend structure

- `src/services/*.service.ts` wrap `apiFetch` (from `src/services/http.ts`) per API domain (auth, admin, analysis, threat intel, user dashboard, mobile money). Prefer adding a method to the relevant service over calling `apiFetch` directly from components.
- `src/stores/` (Pinia) hold client state (auth, analysis, notifications, health, categories, user dashboard).
- `src/router/index.ts` defines two route-meta guards: `requiresAuth` (checks `authService.me()`) and `requiresAdmin` (checks `user.is_admin`), enforced in the global `router.beforeEach`. Admin routes live under `/admin` with `AdminLayout.vue` as the shell and are lazy-loaded.
- `src/views/admin/` are admin-only screens (users, incidents, threat intel, ML model management, integrations, health, audit log, settings); `src/views/user/` are authenticated end-user screens (dashboard, security).
- Path alias `@` → `src/` (configured in both `vite.config.ts` and `tsconfig`).
- Vite dev server proxies `/api` to the Flask backend at `127.0.0.1:5000` — run both servers concurrently for local development.
