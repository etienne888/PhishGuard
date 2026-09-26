"""
Automatic triage of the review queue (user reports + uncertain verdicts).

For every item the engine proposes a label and a confidence:

    confidence = how far the fused score is from the 50 decision line (0-100)
                 x agreement between the independent signals (ML, AI, URL, rules)
                 + a bonus when the Claude analysis is itself confident and agrees

Depending on `triage_mode`:
    manual   -> suggestion only, a human decides everything
    assisted -> the engine closes items whose confidence >= triage_threshold (default 80 %);
                the uncertain rest stays for a human
    auto     -> the engine closes every item; humans can still overturn any decision

Automatic decisions are stored with review_source='auto' so they stay auditable
and are exported separately from human ground truth.
"""
from __future__ import annotations

from datetime import datetime

from app import db
from app.models import Analysis
from app.services import settings_service


def _details(analysis: Analysis) -> dict:
    import json
    raw = analysis.indicators
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    return raw if isinstance(raw, dict) else {}


def suggest(analysis: Analysis) -> tuple[str, float]:
    """Return (label, confidence 0-100) for one analysis."""
    score = float(analysis.score_risk or 0)
    label = 'phishing' if score >= 50 else 'safe'
    details = _details(analysis)

    # 1. Distance from the decision line: 50 -> 0 %, 0 or 100 -> 100 %
    margin = abs(score - 50) * 2

    # 2. Do the independent signals agree with the label?
    signals = [v for v in (details.get('signals') or {}).values() if isinstance(v, (int, float))]
    if signals:
        agreeing = sum(1 for v in signals if (v >= 50) == (label == 'phishing'))
        agreement = agreeing / len(signals)
    else:
        agreement = 0.6
    confidence = margin * (0.55 + 0.45 * agreement)

    # 3. A confident AI that agrees adds certainty; one that disagrees removes it
    ai = details.get('ai') or {}
    if ai.get('classification'):
        ai_label = 'safe' if ai['classification'] == 'legitimate' else 'phishing'
        ai_conf = float(ai.get('confidence') or 0)
        confidence += (0.25 if ai_label == label else -0.35) * ai_conf

    # 4. Hard evidence (blocklist / brand spoof override) is near-certain
    if any('85' in str(o) for o in details.get('overrides') or []):
        confidence = max(confidence, 92)

    # A user report against a "safe" verdict is a reason for human doubt
    if analysis.reported_at and label == 'safe':
        confidence *= 0.7

    return label, round(max(0.0, min(100.0, confidence)), 1)


def triage(analysis: Analysis, commit: bool = True) -> bool:
    """Refresh the suggestion and auto-close the item if the policy allows. Returns True if closed."""
    if analysis.review_label and analysis.review_source != 'auto':
        return False  # never overwrite a human decision
    label, confidence = suggest(analysis)
    analysis.triage_label, analysis.triage_confidence = label, confidence

    mode = settings_service.get('triage_mode')
    threshold = settings_service.get('triage_threshold')
    closed = mode == 'auto' or (mode == 'assisted' and confidence >= threshold)
    if closed:
        analysis.review_label = label
        analysis.review_source = 'auto'
        analysis.reviewed_by = None
        analysis.reviewed_at = datetime.utcnow()
        analysis.review_note = f'Auto-triage ({confidence:.0f} %)'
    elif analysis.review_source == 'auto':
        # policy became stricter: hand the item back to humans
        analysis.review_label = analysis.review_source = analysis.reviewed_at = analysis.review_note = None
    if commit:
        db.session.commit()
    return closed


def queue_query():
    """Items that belong in the review queue: reported, or borderline scores."""
    from sqlalchemy import or_
    return Analysis.query.filter(or_(Analysis.reported_at.isnot(None),
                                     Analysis.score_risk.between(40, 70)))


def run_all() -> dict:
    """Re-triage every open or auto-closed queue item (after a policy change)."""
    items = queue_query().filter(or_review_open()).all()
    closed = sum(triage(a, commit=False) for a in items)
    db.session.commit()
    return {'processed': len(items), 'auto_closed': closed, 'left_for_humans': len(items) - closed}


def or_review_open():
    from sqlalchemy import or_
    return or_(Analysis.review_label.is_(None), Analysis.review_source == 'auto')


def stats() -> dict:
    base = queue_query()
    auto = base.filter(Analysis.review_source == 'auto').count()
    human = base.filter(Analysis.review_label.isnot(None), Analysis.review_source != 'auto').count()
    pending = base.filter(Analysis.review_label.is_(None)).count()
    total = auto + human + pending
    # Accuracy of the engine measured on items a human decided
    judged = Analysis.query.filter(Analysis.review_label.isnot(None),
                                   Analysis.review_source.is_distinct_from('auto')).all()
    correct = sum(1 for a in judged if (a.review_label == 'phishing') == (a.verdict == 'phishing'))
    return {
        'mode': settings_service.get('triage_mode'),
        'threshold': settings_service.get('triage_threshold'),
        'auto_closed': auto, 'human_closed': human, 'pending': pending, 'total': total,
        'automation_rate': round(auto / total * 100, 1) if total else 0,
        'engine_accuracy': round(correct / len(judged) * 100, 1) if judged else None,
        'judged': len(judged),
    }
