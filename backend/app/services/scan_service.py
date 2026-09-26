"""
One place to turn a pipeline result into a stored Analysis, whatever the origin:
the web analyzer, a connected mailbox, or an email forwarded to PhishGuard.

Also owns the "analyse first, sign in to see the result" flow for visitors:
a visitor scan is stored without an owner and with the SHA-256 of a random claim
token; the result is only returned once a signed-in user presents the token.
"""
from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta

from app import db
from app.models import Analysis
from app.services import email_origin

log = logging.getLogger(__name__)

CLAIM_TTL = timedelta(hours=24)
# Keys of the pipeline result kept in analyses.indicators (re-opened by dashboards)
DETAIL_KEYS = ('evidence', 'evidence_positive', 'lang', 'level', 'signals', 'weights', 'overrides', 'ai',
               'recommendation', 'url_details', 'brand', 'origin')


def finalize(result: dict) -> dict:
    """Dashboards count phishing / suspicious / legitimate; keep the 4-level risk as `level`."""
    result['level'] = result['verdict']
    result['verdict'] = {'Critical': 'phishing', 'High': 'phishing',
                         'Medium': 'suspicious'}.get(result['level'], 'legitimate')
    result['url_details'] = result.get('urls', [])
    return result


def save(result: dict, *, user_id: int | None, source: str, text: str = '', mailbox_id: int | None = None,
         external_id: str | None = None, keep_body: bool = True) -> Analysis:
    msg = result.get('message') or {}
    summary = msg.get('subject') or ('.eml' if not text else text)
    analysis = Analysis(
        user_id=user_id,
        # Privacy: safe mailbox emails keep only their subject, never the body
        text_source=(text[:1000] if (text and keep_body) else (msg.get('subject') or summary or '')[:1000]) or '-',
        score_risk=result['score'],
        verdict=result['verdict'],
        indicators=json.dumps({key: result.get(key) for key in DETAIL_KEYS}),
        email_from=(msg.get('sender') or '')[:255] or None,
        subject=(msg.get('subject') or '')[:255] or None,
        urls=[u['url'] for u in result.get('urls', [])],
        duration_ms=result.get('duration_ms'),
        source=source,
        mailbox_id=mailbox_id,
        external_id=external_id,
    )
    db.session.add(analysis)
    db.session.commit()
    post_scan(analysis)
    return analysis


def post_scan(analysis: Analysis) -> None:
    """SOC automation after each scan: triage uncertain verdicts, correlate campaigns."""
    try:
        if 40 <= analysis.score_risk <= 70:
            from app.services.triage_service import triage
            triage(analysis)
        if analysis.verdict in ('phishing', 'suspicious'):
            from app.services.correlation_service import correlate
            correlate()
    except Exception:  # automation must never fail the user's scan
        log.exception('Post-scan automation failed')
        db.session.rollback()


# ---------- visitor claim ----------

def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_claim(analysis: Analysis) -> str:
    token = secrets.token_urlsafe(24)
    analysis.claim_token_hash = _hash(token)
    analysis.claim_expires_at = datetime.utcnow() + CLAIM_TTL
    db.session.commit()
    return token


def claim(token: str, user_id: int) -> Analysis | None:
    if not token or len(token) > 100:
        return None
    analysis = Analysis.query.filter_by(claim_token_hash=_hash(token)).first()
    if analysis is None or analysis.user_id not in (None, user_id):
        return None
    if analysis.claim_expires_at and analysis.claim_expires_at < datetime.utcnow():
        return None
    analysis.user_id = user_id
    analysis.claimed_at = datetime.utcnow()
    analysis.claim_token_hash = None  # single use
    db.session.commit()
    return analysis


def details(analysis: Analysis) -> dict:
    raw = analysis.indicators
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = []
    return raw if isinstance(raw, dict) else {'evidence': raw if isinstance(raw, list) else []}


def to_result(analysis: Analysis) -> dict:
    """Rebuild the /v2/scan response shape from a stored analysis."""
    d = details(analysis)
    return {
        'score': round(float(analysis.score_risk), 2),
        'verdict': analysis.verdict,
        'level': d.get('level'),
        'signals': d.get('signals'),
        'weights': d.get('weights'),
        'overrides': d.get('overrides') or [],
        'evidence': d.get('evidence') or [],
        'evidence_positive': d.get('evidence_positive') or [],
        'recommendation': d.get('recommendation'),
        'ai': d.get('ai'),
        'urls': d.get('url_details') or [{'url': u} for u in (analysis.urls or [])],
        'brand': d.get('brand'),
        'official': official_contact(d.get('brand')),
        # Users only ever get the approximate view (no IPs, no headers); admins use /api/admin/analyses/<id>/origin
        'origin': email_origin.public_view(d.get('origin')),
        'analysis_id': analysis.id,
        'source': analysis.source,
        'text': analysis.text_source,
        'feedback': analysis.feedback,
        'duration_ms': analysis.duration_ms,
        'message': {'sender': analysis.email_from, 'subject': analysis.subject},
    }


def official_contact(brand: str | None) -> dict | None:
    """Official website / hotline of the impersonated institution (from the allowlist)."""
    if not brand:
        return None
    from app.models import WhitelistDomain
    row = (WhitelistDomain.query.filter(WhitelistDomain.institution == brand, WhitelistDomain.is_active.is_(True))
           .order_by(WhitelistDomain.support_contact.is_(None)).first())
    if row is None:
        return {'institution': brand}
    return {'institution': row.institution, 'domain': row.domain, 'website': row.website or f'https://{row.domain}',
            'support_contact': row.support_contact, 'logo_url': row.logo_url}
