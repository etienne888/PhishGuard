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

### Frontend structure

- `src/services/*.service.ts` wrap `apiFetch` (from `src/services/http.ts`) per API domain (auth, admin, analysis, threat intel, user dashboard, mobile money). Prefer adding a method to the relevant service over calling `apiFetch` directly from components.
- `src/stores/` (Pinia) hold client state (auth, analysis, notifications, health, categories, user dashboard).
- `src/router/index.ts` defines two route-meta guards: `requiresAuth` (checks `authService.me()`) and `requiresAdmin` (checks `user.is_admin`), enforced in the global `router.beforeEach`. Admin routes live under `/admin` with `AdminLayout.vue` as the shell and are lazy-loaded.
- `src/views/admin/` are admin-only screens (users, incidents, threat intel, ML model management, integrations, health, audit log, settings); `src/views/user/` are authenticated end-user screens (dashboard, security).
- Path alias `@` → `src/` (configured in both `vite.config.ts` and `tsconfig`).
- Vite dev server proxies `/api` to the Flask backend at `127.0.0.1:5000` — run both servers concurrently for local development.
