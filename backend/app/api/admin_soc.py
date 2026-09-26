"""
Security Operations Centre API (/api/admin/...).

    GET    /system                      live telemetry (API traffic, host, database, engine)
    GET    /soc/summary                 compact counters for the command centre

    GET    /incidents                   list (status / severity filters)
    POST   /incidents                   open an incident manually
    POST   /incidents/correlate         run the correlation engine now
    GET    /incidents/<id>              detail + linked messages
    PATCH  /incidents/<id>              status, severity, assignee, title
    POST   /incidents/<id>/notes        add an analyst note to the timeline
    POST   /incidents/<id>/block        block the incident's domain

    GET    /intel/iocs                  indicators aggregated from real detections
    GET    /intel/summary               targeted brands, threat categories, feed status
    POST   /intel/feed/refresh          re-download the OpenPhish feed

    GET    /blocklist                   blocked domains
    POST   /blocklist                   block a domain
    DELETE /blocklist/<id>              unblock (sudo)
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from flask import Blueprint, request
from flask_login import current_user

from app import db
from app.api.admin import admin_required
from app.api.responses import err, ok
from app.api.security import sudo_required
from app.models import Analysis, BlockedDomain, Incident, User
from app.pipeline.sender import load_whitelist, registered_domain
from app.services import audit_service, correlation_service, indicators, system_metrics, threat_feed, triage_service

admin_soc_bp = Blueprint('admin_soc', __name__)

STATUSES = {'open', 'investigating', 'contained', 'resolved', 'false_positive'}
SEVERITIES = {'critical', 'high', 'medium', 'low'}
DOMAIN_RE = re.compile(r'^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$')


def _user_names(ids) -> dict[int, str]:
    ids = {i for i in ids if i}
    return {u.id: (u.full_name or u.email) for u in User.query.filter(User.id.in_(ids)).all()} if ids else {}


# ------------------------------------------------------------ System ----

@admin_soc_bp.route('/system', methods=['GET'])
@admin_required
def system():
    return ok(system_metrics.snapshot())


@admin_soc_bp.route('/soc/summary', methods=['GET'])
@admin_required
def soc_summary():
    open_incidents = Incident.query.filter(Incident.status.in_(correlation_service.OPEN_STATUSES))
    snapshot = system_metrics.snapshot()
    return ok({
        'incidents': {
            'open': open_incidents.count(),
            'critical': open_incidents.filter(Incident.severity == 'critical').count(),
            'latest': [correlation_service.serialize(i) for i in
                       open_incidents.order_by(Incident.updated_at.desc()).limit(4).all()],
        },
        'triage': triage_service.stats(),
        'blocked_domains': BlockedDomain.query.filter_by(is_active=True).count(),
        'pending_accounts': User.query.filter(User.approval_status.in_(('pending', 'review'))).count(),
        'system': {'status': snapshot['status'], 'problems': snapshot['problems'],
                   'db_latency_ms': snapshot['database'].get('latency_ms'),
                   'p95_ms': snapshot['traffic']['p95_ms'], 'rpm': snapshot['traffic']['rpm'],
                   'error_rate': snapshot['traffic']['error_rate'],
                   'cpu': snapshot['host'].get('cpu_percent'), 'memory': snapshot['host'].get('memory_percent'),
                   'pipeline_p50_ms': snapshot['engine']['pipeline_p50_ms'],
                   'ai_coverage': snapshot['engine']['ai_coverage']},
    })


# --------------------------------------------------------- Incidents ----

@admin_soc_bp.route('/incidents', methods=['GET'])
@admin_required
def list_incidents():
    query = Incident.query
    status = request.args.get('status')
    if status == 'active':
        query = query.filter(Incident.status.in_(correlation_service.OPEN_STATUSES))
    elif status in STATUSES:
        query = query.filter(Incident.status == status)
    if request.args.get('severity') in SEVERITIES:
        query = query.filter(Incident.severity == request.args['severity'])
    rows = query.order_by(Incident.updated_at.desc()).limit(200).all()
    names = _user_names(r.assigned_to for r in rows)
    all_rows = Incident.query.all()
    week_ago = datetime.utcnow() - timedelta(days=7)
    resolved = [i for i in all_rows if i.resolved_at and i.created_at]
    mttr_hours = (sum((i.resolved_at - i.created_at).total_seconds() for i in resolved) / len(resolved) / 3600
                  if resolved else None)
    return ok({
        'items': [correlation_service.serialize(r, names) for r in rows],
        'stats': {
            'open': sum(1 for i in all_rows if i.status == 'open'),
            'investigating': sum(1 for i in all_rows if i.status == 'investigating'),
            'contained': sum(1 for i in all_rows if i.status == 'contained'),
            'resolved_7d': sum(1 for i in all_rows if i.resolved_at and i.resolved_at >= week_ago),
            'critical_active': sum(1 for i in all_rows if i.severity == 'critical'
                                   and i.status in correlation_service.OPEN_STATUSES),
            'mttr_hours': round(mttr_hours, 1) if mttr_hours is not None else None,
        },
    })


@admin_soc_bp.route('/incidents', methods=['POST'])
@admin_required
def create_incident():
    data = request.get_json(silent=True) or {}
    title = ' '.join((data.get('title') or '').split())[:255]
    if len(title) < 4:
        return err('INVALID_TITLE', 'Titre requis (4 caractères minimum).')
    severity = data.get('severity') if data.get('severity') in SEVERITIES else 'medium'
    indicator = (data.get('indicator') or '').strip().lower()[:255] or None
    incident = Incident(ref=correlation_service.next_ref(), title=title, severity=severity, source='manual',
                        indicator=indicator, indicator_type='domain' if indicator and '.' in indicator else None,
                        category=(data.get('category') or 'other')[:60], analysis_ids=[], timeline=[],
                        assigned_to=current_user.id, first_seen=datetime.utcnow(), last_seen=datetime.utcnow())
    db.session.add(incident)
    db.session.flush()
    correlation_service.add_event(incident, 'opened', (data.get('description') or '')[:2000],
                                  actor=current_user.email)
    db.session.commit()
    audit_service.record('admin_incident_opened', details={'ref': incident.ref})
    return ok(correlation_service.serialize(incident, _user_names([incident.assigned_to])), status=201)


@admin_soc_bp.route('/incidents/correlate', methods=['POST'])
@admin_required
def run_correlation():
    result = correlation_service.correlate(window_hours=request.args.get('hours', type=int))
    audit_service.record('admin_correlation_run', details=result)
    return ok(result)


def _incident_or_404(incident_id: int):
    incident = db.session.get(Incident, incident_id)
    return incident, (None if incident else err('NOT_FOUND', 'Incident introuvable.', 404))


@admin_soc_bp.route('/incidents/<int:incident_id>', methods=['GET'])
@admin_required
def get_incident(incident_id: int):
    incident, missing = _incident_or_404(incident_id)
    if missing:
        return missing
    analyses = (Analysis.query.filter(Analysis.id.in_(incident.analysis_ids or []))
                .order_by(Analysis.created_at.desc()).limit(100).all())
    names = _user_names([incident.assigned_to, *[a.user_id for a in analyses]])
    return ok({
        **correlation_service.serialize(incident, names),
        'messages_detail': [{
            'id': a.id, 'preview': a.text_source[:160], 'score': round(float(a.score_risk), 1),
            'verdict': a.verdict, 'user': names.get(a.user_id), 'created_at': a.created_at.isoformat(),
            'urls': (a.urls or [])[:5],
        } for a in analyses],
        'admins': [{'id': u.id, 'name': u.full_name or u.email} for u in User.query.filter_by(is_admin=True).all()],
    })


@admin_soc_bp.route('/incidents/<int:incident_id>', methods=['PATCH'])
@admin_required
def update_incident(incident_id: int):
    incident, missing = _incident_or_404(incident_id)
    if missing:
        return missing
    data = request.get_json(silent=True) or {}
    actor = current_user.email
    if data.get('status') in STATUSES and data['status'] != incident.status:
        correlation_service.add_event(incident, 'status', f"{incident.status} → {data['status']}", actor=actor)
        incident.status = data['status']
        incident.resolved_at = datetime.utcnow() if data['status'] in ('resolved', 'false_positive') else None
        if data['status'] == 'false_positive':
            # Teach the engine: the linked messages were not phishing
            for a in Analysis.query.filter(Analysis.id.in_(incident.analysis_ids or [])).all():
                if not a.review_label:
                    a.review_label, a.review_source = 'safe', 'admin'
                    a.reviewed_by, a.reviewed_at = current_user.id, datetime.utcnow()
    if data.get('severity') in SEVERITIES and data['severity'] != incident.severity:
        correlation_service.add_event(incident, 'severity', f"{incident.severity} → {data['severity']}", actor=actor)
        incident.severity = data['severity']
    if 'assigned_to' in data:
        assignee = db.session.get(User, data['assigned_to']) if data['assigned_to'] else None
        if data['assigned_to'] and (not assignee or not assignee.is_admin):
            return err('INVALID_ASSIGNEE', 'Seul un administrateur peut être assigné.')
        incident.assigned_to = assignee.id if assignee else None
        correlation_service.add_event(incident, 'assigned', assignee.email if assignee else '—', actor=actor)
    if data.get('title'):
        incident.title = ' '.join(data['title'].split())[:255]
    db.session.commit()
    audit_service.record('admin_incident_updated', details={'ref': incident.ref, 'fields': sorted(data)})
    return ok(correlation_service.serialize(incident, _user_names([incident.assigned_to])))


@admin_soc_bp.route('/incidents/<int:incident_id>/notes', methods=['POST'])
@admin_required
def add_note(incident_id: int):
    incident, missing = _incident_or_404(incident_id)
    if missing:
        return missing
    text = ((request.get_json(silent=True) or {}).get('text') or '').strip()[:2000]
    if not text:
        return err('EMPTY_NOTE', 'La note est vide.')
    correlation_service.add_event(incident, 'note', text, actor=current_user.email)
    db.session.commit()
    return ok(correlation_service.serialize(incident, _user_names([incident.assigned_to])))


@admin_soc_bp.route('/incidents/<int:incident_id>/block', methods=['POST'])
@admin_required
def block_incident(incident_id: int):
    incident, missing = _incident_or_404(incident_id)
    if missing:
        return missing
    if incident.indicator_type != 'domain' or not incident.indicator:
        return err('NOT_A_DOMAIN', "Cet incident n'est pas lié à un domaine.")
    correlation_service.block(incident.indicator, f'Incident {incident.ref}', incident=incident, actor_id=current_user.id)
    if incident.status == 'open':
        correlation_service.add_event(incident, 'status', 'open → contained', actor=current_user.email)
        incident.status = 'contained'
    db.session.commit()
    audit_service.record('admin_domain_blocked', details={'domain': incident.indicator, 'ref': incident.ref},
                         severity='warning')
    return ok(correlation_service.serialize(incident, _user_names([incident.assigned_to])))


# ------------------------------------------------ Threat intelligence ----

@admin_soc_bp.route('/intel/iocs', methods=['GET'])
@admin_required
def iocs():
    """Every indicator seen in dangerous messages, aggregated, enriched with OpenPhish and the blocklist."""
    days = min(365, max(1, request.args.get('days', default=30, type=int)))
    since = datetime.utcnow() - timedelta(days=days)
    whitelist = load_whitelist()
    feed = threat_feed.load()
    blocked = {b.domain for b in BlockedDomain.query.filter_by(is_active=True).all()}
    geo_cache = _geo_cache()

    agg: dict[tuple[str, str], dict] = {}
    users: dict[tuple[str, str], set] = defaultdict(set)
    rows = Analysis.query.filter(Analysis.created_at >= since, Analysis.verdict.in_(('phishing', 'suspicious')),
                                 Analysis.review_label.is_distinct_from('safe')).all()
    for a in rows:
        for kind, value in set(indicators.extract(a, whitelist)):
            item = agg.setdefault((kind, value), {'type': kind, 'value': value, 'hits': 0, 'max_score': 0,
                                                  'first_seen': a.created_at, 'last_seen': a.created_at,
                                                  'analysis_ids': []})
            item['hits'] += 1
            item['max_score'] = max(item['max_score'], float(a.score_risk))
            item['first_seen'] = min(item['first_seen'], a.created_at)
            item['last_seen'] = max(item['last_seen'], a.created_at)
            if len(item['analysis_ids']) < 20:
                item['analysis_ids'].append(a.id)
            if a.user_id:
                users[(kind, value)].add(a.user_id)

    week_ago = datetime.utcnow() - timedelta(days=7)
    items = []
    for key, item in agg.items():
        kind, value = key
        domain = registered_domain(indicators.host_of(value)) if kind == 'url' else value if kind in ('domain', 'sender') else None
        geo = geo_cache.get(indicators.host_of(value) if kind == 'url' else value) or {}
        items.append({
            **item,
            'id': f'{kind}:{value}',
            'max_score': round(item['max_score'], 1),
            'confidence': min(100, round(item['max_score'] * 0.7 + min(item['hits'], 10) * 3)),
            'severity': 'critical' if item['max_score'] >= 90 else 'high' if item['max_score'] >= 75 else 'medium',
            'users': len(users[key]),
            'active': item['last_seen'] >= week_ago,
            'openphish': bool(domain and domain in feed['domains']),
            'blocked': bool(domain and domain in blocked),
            'country': geo.get('country'), 'isp': geo.get('isp'),
            'first_seen': item['first_seen'].isoformat(), 'last_seen': item['last_seen'].isoformat(),
        })
    items.sort(key=lambda i: (i['type'] != 'domain', -i['hits'], -i['max_score']))
    return ok({'items': items, 'total': len(items), 'days': days, 'analyses_scanned': len(rows),
               'feed': {'ok': feed['ok'], 'size': len(feed['urls']),
                        'fetched_at': datetime.utcfromtimestamp(feed['fetched_at']).isoformat() if feed['fetched_at'] else None}})


def _geo_cache() -> dict:
    """Server locations already resolved for the threat map (instance/geo_cache.json)."""
    import json
    import os
    from flask import current_app
    try:
        with open(os.path.join(current_app.instance_path, 'geo_cache.json'), encoding='utf-8') as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        return {}
    return {host: (entry.get('data') or entry) for host, entry in raw.items() if isinstance(entry, dict)}


@admin_soc_bp.route('/intel/summary', methods=['GET'])
@admin_required
def intel_summary():
    days = min(365, max(1, request.args.get('days', default=30, type=int)))
    since = datetime.utcnow() - timedelta(days=days)
    rows = Analysis.query.filter(Analysis.created_at >= since, Analysis.verdict.in_(('phishing', 'suspicious'))).all()
    brands, categories, daily = Counter(), Counter(), Counter()
    for a in rows:
        brands.update(indicators.brands(a))
        category = (indicators.details(a).get('ai') or {}).get('category')
        if category:
            categories[category] += 1
        daily[a.created_at.date().isoformat()] += 1
    feed = threat_feed.load()
    return ok({
        'days': days, 'dangerous_messages': len(rows),
        'brands': [{'name': b, 'count': n} for b, n in brands.most_common(8)],
        'categories': [{'name': c, 'count': n} for c, n in categories.most_common(10)],
        'daily': [{'date': (since + timedelta(days=i)).date().isoformat(),
                   'count': daily.get((since + timedelta(days=i)).date().isoformat(), 0)} for i in range(days + 1)][-30:],
        'feed': {'name': 'OpenPhish', 'ok': feed['ok'], 'size': len(feed['urls']),
                 'fetched_at': datetime.utcfromtimestamp(feed['fetched_at']).isoformat() if feed['fetched_at'] else None,
                 'sample': feed['urls'][:8]},
    })


@admin_soc_bp.route('/intel/feed/refresh', methods=['POST'])
@admin_required
def refresh_feed():
    feed = threat_feed.load(force=True)
    return ok({'ok': feed['ok'], 'size': len(feed['urls'])})


# ---------------------------------------------------------- Blocklist ----

def _serialize_block(row: BlockedDomain, names: dict) -> dict:
    return {'id': row.id, 'domain': row.domain, 'reason': row.reason, 'incident_id': row.incident_id,
            'created_by': names.get(row.created_by), 'is_active': row.is_active,
            'created_at': row.created_at.isoformat() if row.created_at else None}


@admin_soc_bp.route('/blocklist', methods=['GET'])
@admin_required
def list_blocklist():
    rows = BlockedDomain.query.order_by(BlockedDomain.created_at.desc()).all()
    names = _user_names(r.created_by for r in rows)
    return ok({'items': [_serialize_block(r, names) for r in rows], 'total': len(rows)})


@admin_soc_bp.route('/blocklist', methods=['POST'])
@admin_required
def add_blocklist():
    data = request.get_json(silent=True) or {}
    domain = re.sub(r'^https?://', '', (data.get('domain') or '').strip().lower()).split('/')[0].removeprefix('www.')
    if not DOMAIN_RE.match(domain):
        return err('INVALID_DOMAIN', 'Nom de domaine invalide.')
    if domain in load_whitelist() or registered_domain(domain) in load_whitelist():
        return err('ALLOWLISTED', "Ce domaine est dans la liste blanche : retirez-le d'abord.", 409)
    row = correlation_service.block(domain, (data.get('reason') or '')[:500] or None, actor_id=current_user.id)
    db.session.commit()
    audit_service.record('admin_domain_blocked', details={'domain': domain}, severity='warning')
    return ok(_serialize_block(row, _user_names([row.created_by])), status=201)


@admin_soc_bp.route('/blocklist/<int:row_id>', methods=['DELETE'])
@admin_required
@sudo_required
def remove_blocklist(row_id: int):
    row = db.session.get(BlockedDomain, row_id)
    if not row:
        return err('NOT_FOUND', 'Entrée introuvable.', 404)
    domain = row.domain
    db.session.delete(row)
    db.session.commit()
    audit_service.record('admin_domain_unblocked', details={'domain': domain}, severity='warning')
    return ok({'deleted': True})
