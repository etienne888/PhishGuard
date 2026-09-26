"""Public endpoints (no sign-in): community scam alerts for the landing page and dashboard."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from flask import Blueprint

from app.api.responses import ok
from app.models import Analysis, Incident, User

public_bp = Blueprint('public', __name__)

ACTIVE = ('open', 'investigating', 'contained')


def _defang(value: str) -> str:
    """mtn-secure.tk -> mtn-secure[.]tk: readable, but no longer a clickable link."""
    return value.replace('.', '[.]') if value else value


@public_bp.route('/alerts', methods=['GET'])
def community_alerts():
    """Active scam campaigns of the last 14 days, anonymised (brand/domain, regions, volume)."""
    since = datetime.utcnow() - timedelta(days=14)
    incidents = (Incident.query.filter(Incident.status.in_(ACTIVE), Incident.last_seen >= since)
                 .order_by(Incident.last_seen.desc()).limit(6).all())
    items = []
    for inc in incidents:
        ids = (inc.analysis_ids or [])[:200]
        regions = Counter()
        if ids:
            rows = (User.query.join(Analysis, Analysis.user_id == User.id)
                    .filter(Analysis.id.in_(ids), User.region.isnot(None)).with_entities(User.region).all())
            regions.update(r[0] for r in rows)
        items.append({
            'id': inc.id,
            'kind': inc.indicator_type or 'domain',
            'label': _defang(inc.indicator) if inc.indicator_type == 'domain' else inc.indicator,
            'category': inc.category,
            'severity': inc.severity,
            'messages': len(inc.analysis_ids or []),
            'regions': [name for name, _ in regions.most_common(2)],
            'last_seen': inc.last_seen.isoformat() if inc.last_seen else None,
        })
    return ok({'items': items})
