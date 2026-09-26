"""
Incident correlation engine.

A single phishing message is an alert; several dangerous messages sharing the
same malicious domain or impersonating the same brand within a time window are
a campaign. When `incident_threshold` messages (default 3) share an indicator
within `incident_window_hours` (default 72 h) an incident is opened, or the
existing open incident on that indicator is updated.

Severity: critical if the max score >= 90 or >= 10 messages or >= 5 people hit,
high >= 75, medium otherwise. Everything that happens is appended to the
incident timeline so an analyst can replay the investigation.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from app import db
from app.models import Analysis, BlockedDomain, Incident
from app.pipeline.sender import load_whitelist
from app.services import indicators, settings_service

OPEN_STATUSES = ('open', 'investigating', 'contained')
CORRELATED_TYPES = ('domain', 'brand')


def _severity(max_score: float, count: int, users: int) -> str:
    if max_score >= 90 or count >= 10 or users >= 5:
        return 'critical'
    if max_score >= 75:
        return 'high'
    return 'medium'


def next_ref() -> str:
    year = datetime.utcnow().year
    count = Incident.query.filter(Incident.ref.like(f'INC-{year}-%')).count()
    return f'INC-{year}-{count + 1:04d}'


def add_event(incident: Incident, kind: str, text: str, actor: str | None = None, **extra):
    """Append to the timeline (JSON list; reassigned so SQLAlchemy sees the change)."""
    incident.timeline = [*(incident.timeline or []), {
        'at': datetime.utcnow().isoformat(), 'kind': kind, 'text': text, 'actor': actor, **extra,
    }]
    incident.updated_at = datetime.utcnow()


def correlate(window_hours: int | None = None) -> dict:
    """Scan recent dangerous analyses and open / update incidents. Returns counts."""
    threshold = settings_service.get('incident_threshold') or 3
    hours = window_hours or settings_service.get('incident_window_hours') or 72
    since = datetime.utcnow() - timedelta(hours=hours)
    whitelist = load_whitelist()

    groups: dict[tuple[str, str], list[Analysis]] = defaultdict(list)
    rows = Analysis.query.filter(Analysis.created_at >= since,
                                 Analysis.verdict.in_(('phishing', 'suspicious')),
                                 Analysis.review_label.is_distinct_from('safe')).all()
    for a in rows:
        for kind, value in set(indicators.extract(a, whitelist)):
            if kind in CORRELATED_TYPES:
                groups[(kind, value)].append(a)

    opened = updated = 0
    for (kind, value), items in groups.items():
        if len(items) < threshold:
            continue
        ids = sorted({a.id for a in items})
        users = len({a.user_id for a in items if a.user_id})
        max_score = max(float(a.score_risk) for a in items)
        first, last = min(a.created_at for a in items), max(a.created_at for a in items)

        incident = (Incident.query.filter(Incident.indicator == value, Incident.status.in_(OPEN_STATUSES))
                    .order_by(Incident.created_at.desc()).first())
        if incident is None:
            incident = Incident(
                ref=next_ref(), source='auto', indicator=value, indicator_type=kind,
                title=(f'Campagne via {value}' if kind == 'domain' else f'Usurpation de {value}'),
                category='brand_impersonation' if kind == 'brand' else 'malicious_domain',
                analysis_ids=ids, affected_users=users, max_score=max_score,
                severity=_severity(max_score, len(ids), users), first_seen=first, last_seen=last,
                timeline=[],
            )
            db.session.add(incident)
            db.session.flush()  # get an id before linking a blocklist entry
            add_event(incident, 'opened', f'{len(ids)} messages · {kind}: {value}', count=len(ids))
            if kind == 'domain' and settings_service.get('auto_block_incidents'):
                block(value, f'Auto-block ({incident.ref})', incident=incident)
            opened += 1
        else:
            new_ids = sorted(set(ids) - set(incident.analysis_ids or []))
            if not new_ids:
                continue
            incident.analysis_ids = sorted(set(incident.analysis_ids or []) | set(ids))
            incident.affected_users = max(incident.affected_users, users)
            incident.max_score = max(incident.max_score, max_score)
            incident.last_seen = max(incident.last_seen or last, last)
            new_severity = _severity(incident.max_score, len(incident.analysis_ids), incident.affected_users)
            if new_severity != incident.severity and new_severity == 'critical':
                add_event(incident, 'escalated', 'critical')
            incident.severity = new_severity
            add_event(incident, 'linked', f'+{len(new_ids)}', count=len(new_ids), analysis_ids=new_ids)
            updated += 1
    db.session.commit()
    return {'opened': opened, 'updated': updated, 'indicators_checked': len(groups)}


def block(domain: str, reason: str, incident: Incident | None = None, actor_id: int | None = None) -> BlockedDomain:
    domain = domain.lower().strip()
    row = BlockedDomain.query.filter_by(domain=domain).first()
    if row is None:
        row = BlockedDomain(domain=domain, reason=reason, created_by=actor_id,
                            incident_id=incident.id if incident and incident.id else None)
        db.session.add(row)
    row.is_active = True
    if incident is not None:
        add_event(incident, 'blocked', domain)
    return row


def serialize(incident: Incident, users: dict[int, str] | None = None) -> dict:
    users = users or {}
    return {
        'id': incident.id, 'ref': incident.ref, 'title': incident.title,
        'indicator': incident.indicator, 'indicator_type': incident.indicator_type,
        'category': incident.category, 'severity': incident.severity, 'status': incident.status,
        'source': incident.source, 'analysis_ids': incident.analysis_ids or [],
        'messages': len(incident.analysis_ids or []), 'affected_users': incident.affected_users,
        'max_score': round(incident.max_score or 0, 1),
        'assigned_to': incident.assigned_to, 'assignee': users.get(incident.assigned_to),
        'blocked': bool(incident.indicator and BlockedDomain.query.filter_by(domain=incident.indicator, is_active=True).first()),
        'timeline': incident.timeline or [],
        'first_seen': incident.first_seen.isoformat() if incident.first_seen else None,
        'last_seen': incident.last_seen.isoformat() if incident.last_seen else None,
        'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
        'created_at': incident.created_at.isoformat() if incident.created_at else None,
        'updated_at': incident.updated_at.isoformat() if incident.updated_at else None,
    }
