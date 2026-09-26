"""Email origin investigation and the threat radar (admin) - mounted on /api/admin."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from flask import Blueprint, request

from app.api.admin import admin_required
from app.api.responses import err, ok
from app.models import Analysis, User
from app.pipeline.i18n import request_lang, tr
from app.services import audit_service, scan_service

admin_geo_bp = Blueprint('admin_geo', __name__)
RANK = {'legitimate': 0, 'suspicious': 1, 'phishing': 2}


def _origin(analysis: Analysis) -> dict | None:
    origin = scan_service.details(analysis).get('origin')
    return origin if isinstance(origin, dict) else None


def _summary(a: Analysis) -> dict:
    return {'id': a.id, 'subject': a.subject, 'sender': a.email_from, 'verdict': a.verdict,
            'score': round(float(a.score_risk)), 'source': a.source,
            'created_at': a.created_at.isoformat() if a.created_at else None}


@admin_geo_bp.route('/analyses/<int:analysis_id>/origin', methods=['GET'])
@admin_required
def analysis_origin(analysis_id: int):
    """Full origin report of one email: route, hops, sender IP intelligence, device, pivots. Audited."""
    analysis = Analysis.query.get(analysis_id)
    if analysis is None:
        return err('NOT_FOUND', tr(request_lang(), 'error.not_found'), 404)
    origin = _origin(analysis)
    pivots = {'same_ip': [], 'same_network': []}
    if origin and origin.get('sender_ip'):
        ip, asn = origin['sender_ip'], (origin.get('geo') or {}).get('asn')
        since = datetime.utcnow() - timedelta(days=90)
        for other in (Analysis.query.filter(Analysis.id != analysis.id, Analysis.created_at >= since,
                                            Analysis.source.in_(('mailbox', 'forward', 'web')))
                      .order_by(Analysis.created_at.desc()).limit(3000)):
            o = _origin(other)
            if not o:
                continue
            if o.get('sender_ip') == ip and len(pivots['same_ip']) < 20:
                pivots['same_ip'].append(_summary(other))
            elif asn and (o.get('geo') or {}).get('asn') == asn and len(pivots['same_network']) < 20:
                pivots['same_network'].append(_summary(other))
    owner = User.query.get(analysis.user_id) if analysis.user_id else None
    # Sender IPs are personal data: every view is written to the audit trail
    audit_service.record('admin_origin_viewed', user_id=analysis.user_id,
                         details={'analysis_id': analysis.id, 'sender_ip': (origin or {}).get('sender_ip')})
    return ok({'analysis': {**_summary(analysis), 'owner': owner.email if owner else None},
               'origin': origin, 'pivots': pivots})


@admin_geo_bp.route('/origin-map', methods=['GET'])
@admin_required
def origin_map():
    """Where analysed emails were really sent from, grouped by approximate place (~1 km)."""
    days = min(365, max(1, request.args.get('days', default=30, type=int)))
    scope = request.args.get('scope', 'threats')
    since = datetime.utcnow() - timedelta(days=days)
    places: dict[tuple, dict] = {}
    totals = Counter()
    rows = (Analysis.query.filter(Analysis.created_at >= since, Analysis.source.in_(('mailbox', 'forward', 'web')))
            .order_by(Analysis.created_at.desc()).limit(3000).all())
    for a in rows:
        origin = _origin(a)
        if not origin:
            continue
        totals['traced'] += 1
        if origin.get('precision') == 'hidden':
            totals['hidden'] += 1
            totals[f"hidden:{origin.get('provider') or '?'}"] += 1
            continue
        geo = origin.get('geo') or {}
        if geo.get('lat') is None or (scope == 'threats' and a.verdict == 'legitimate'):
            continue
        key = (round(geo['lat'], 2), round(geo['lon'], 2))
        place = places.setdefault(key, {
            'id': f'{key[0]},{key[1]}', 'lat': key[0], 'lon': key[1], 'city': geo.get('city'),
            'district': geo.get('district'), 'region': geo.get('region'), 'country': geo.get('country'),
            'country_code': geo.get('country_code'), 'count': 0, 'verdict': 'legitimate', 'max_score': 0,
            'isps': Counter(), 'ips': Counter(), 'flags': Counter(), 'network_types': Counter(),
            'brands': Counter(), 'accuracy_km': origin.get('accuracy_km'), 'analyses': [], 'last_seen': None,
            'first_seen': None, 'routes': []})
        place['count'] += 1
        place['max_score'] = max(place['max_score'], round(float(a.score_risk)))
        if RANK.get(a.verdict, 0) > RANK.get(place['verdict'], 0):
            place['verdict'] = a.verdict
        place['isps'][geo.get('isp') or '?'] += 1
        place['ips'][origin.get('sender_ip')] += 1
        place['network_types'][origin.get('network_type') or '?'] += 1
        place['flags'].update(origin.get('flags') or [])
        if origin.get('claimed_brand'):
            place['brands'][origin['claimed_brand']] += 1
        when = a.created_at.isoformat() if a.created_at else None
        place['last_seen'] = place['last_seen'] or when
        place['first_seen'] = when
        if len(place['analyses']) < 25:
            place['analyses'].append(_summary(a))
        if len(place['routes']) < 3 and len(origin.get('route') or []) > 1:
            place['routes'].append(origin['route'])
    points = []
    for p in places.values():
        for key in ('isps', 'ips', 'flags', 'network_types', 'brands'):
            p[key] = [{'name': k, 'count': n} for k, n in p[key].most_common(6)]
        points.append(p)
    points.sort(key=lambda p: (-RANK.get(p['verdict'], 0), -p['count']))
    hidden_by = [{'provider': k.split(':', 1)[1], 'count': n} for k, n in totals.items() if k.startswith('hidden:')]
    return ok({'days': days, 'scope': scope, 'points': points[:500], 'traced': totals['traced'],
               'hidden': totals['hidden'], 'hidden_by': sorted(hidden_by, key=lambda h: -h['count']),
               'countries': [{'country': c, 'count': n} for c, n in
                             Counter(p['country'] for p in points for _ in range(p['count'])).most_common(8)],
               'generated_at': datetime.utcnow().isoformat()})
