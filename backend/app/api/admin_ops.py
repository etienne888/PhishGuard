"""
Admin operations on real data:
  - /overview        live platform statistics
  - /review-queue    user reports + borderline scores, admin decisions, CSV export
  - /whitelist       Cameroonian institutions whitelist (used by the detection pipeline)
"""
from __future__ import annotations

import csv
import io
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import Blueprint, Response, request
from flask_login import current_user

from app import db
from app.api.admin import admin_required
from app.api.responses import err, ok
from app.api.user_dashboard import _analysis_detail, _analysis_status, _details, _message
from app.models import Analysis, User, WhitelistDomain

admin_ops_bp = Blueprint('admin_ops', __name__)

BORDERLINE = (40, 70)  # scores the engine is least sure about
REVIEW_LABELS = {'phishing', 'safe'}
WHITELIST_CATEGORIES = {'mobile_money', 'banking', 'telecom', 'government', 'other'}
DOMAIN_RE = re.compile(r'^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$')
BRAND_RE = re.compile(r"(?:imite|nom de) ([A-ZÀ-Ý][\w'’À-ÿ\- ]+?)(?: sans| \(|\s*:|$)")


def _source(analysis: Analysis) -> str:
    return analysis.user.email if analysis.user else 'Visiteur (page d’accueil)'


def _queue_item(analysis: Analysis) -> dict:
    return {
        **_message(analysis),
        'source': _source(analysis),
        'report_note': analysis.report_note,
        'reviewed_at': analysis.reviewed_at.isoformat() if analysis.reviewed_at else None,
        'review_note': analysis.review_note,
        'reviewer': db.session.get(User, analysis.reviewed_by).email if analysis.reviewed_by else None,
        'reason': 'reported' if analysis.reported_at else 'borderline',
    }


ENGINE_NAME = os.getenv('ENGINE_NAME', 'PhishGuard-XGB v2.4.1')
CAMEROON_HQ = {'lat': 3.848, 'lon': 11.5021, 'label': 'Yaoundé, Cameroun'}


def _engine_info() -> dict:
    from app.pipeline import _load_ml_model
    from app.pipeline.url_intel import get_xgb_model, xgb_enabled
    xgb_trained = get_xgb_model() is not None
    return {
        'name': ENGINE_NAME,
        'components': [
            {'key': 'xgb', 'label': 'XGBoost (liens)', 'active': xgb_trained and xgb_enabled(),
             'note': None if xgb_enabled() else ('biais détecté — à réentraîner' if xgb_trained else 'non entraîné')},
            {'key': 'nb', 'label': 'Naive Bayes (texte)', 'active': _load_ml_model() is not None},
            {'key': 'rules', 'label': 'Règles expertes CM', 'active': True},
            {'key': 'ai', 'label': os.getenv('CLAUDE_MODEL', 'claude-opus-5'), 'active': bool(os.getenv('ANTHROPIC_API_KEY'))},
        ],
        'ai_enabled': bool(os.getenv('ANTHROPIC_API_KEY')),
        'ai_model': os.getenv('CLAUDE_MODEL', 'claude-opus-5'),
        'whitelist_domains': WhitelistDomain.query.filter_by(is_active=True).count(),
    }


# ----------------------------------------------------------- Threat map ----

@admin_ops_bp.route('/threat-map', methods=['GET'])
@admin_required
def threat_map():
    """Where the malicious links found in recent analyses are hosted (IP geolocation)."""
    from app.services.geo_service import locate_hosts

    from app.pipeline.parser import extract_urls

    days = min(90, max(1, request.args.get('days', default=30, type=int)))
    include_safe = request.args.get('scope') == 'all'
    since = datetime.utcnow() - timedelta(days=days)
    hosts: dict[str, dict] = {}
    rows = (Analysis.query.filter(Analysis.created_at >= since)
            .order_by(Analysis.created_at.desc()).limit(1000).all())
    rank = {'safe': 0, 'suspicious': 1, 'phishing': 2}
    for a in rows:
        status = _analysis_status(a.verdict)
        if status == 'safe' and not include_safe:
            continue
        # Analyses from the old /api/analyze endpoint never stored their links
        for url in (a.urls or extract_urls(a.text_source or '')):
            host = (urlparse(url if '://' in url else f'http://{url}').hostname or '').lower()
            if not host:
                continue
            entry = hosts.setdefault(host, {'host': host, 'count': 0, 'max_score': 0, 'status': status,
                                            'last_seen': None, 'analysis_ids': []})
            entry['count'] += 1
            entry['max_score'] = max(entry['max_score'], round(float(a.score_risk)))
            if rank[status] > rank[entry['status']]:
                entry['status'] = status  # a host keeps its worst verdict
            if entry['last_seen'] is None:
                entry['last_seen'] = a.created_at.isoformat() if a.created_at else None
            if len(entry['analysis_ids']) < 5:
                entry['analysis_ids'].append(a.id)

    ranked = sorted(hosts.values(), key=lambda h: (-rank[h['status']], -h['count'], -h['max_score']))[:100]
    located = locate_hosts([h['host'] for h in ranked], retry_failed=request.args.get('retry') == '1')
    points, unlocated = [], []
    for h in ranked:
        geo = located.get(h['host'])
        (points if geo else unlocated).append({**h, **({k: geo[k] for k in (
            'ip', 'lat', 'lon', 'city', 'country', 'country_code', 'isp', 'asn')} if geo else {})})

    countries = Counter(p['country'] for p in points for _ in range(p['count']))
    return ok({
        'target': CAMEROON_HQ,
        'days': days,
        'scope': 'all' if include_safe else 'threats',
        'analyses_scanned': len(rows),
        'points': points,
        'unlocated': unlocated,
        'countries': [{'country': c, 'count': n} for c, n in countries.most_common(8)],
        'generated_at': datetime.utcnow().isoformat(),
    })


# ------------------------------------------------------------- Overview ----

@admin_ops_bp.route('/overview', methods=['GET'])
@admin_required
def overview():
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    since = today - timedelta(days=13)

    status_totals = Counter(_analysis_status(v) for (v,) in db.session.query(Analysis.verdict).all())
    total = sum(status_totals.values())

    # Daily series and top indicators over the last 14 days
    days = {(since + timedelta(days=i)).date().isoformat(): Counter() for i in range(14)}
    domains, brands = Counter(), Counter()
    recent_rows = Analysis.query.filter(Analysis.created_at >= since).all()
    for a in recent_rows:
        status = _analysis_status(a.verdict)
        key = a.created_at.date().isoformat()
        if key in days:
            days[key][status] += 1
        if status == 'safe':
            continue
        for url in a.urls or []:
            host = (urlparse(url if '://' in url else f'http://{url}').hostname or '').lower()
            if host:
                domains[host] += 1
        for item in _details(a).get('evidence', []):
            if str(item).startswith('IA :'):
                continue  # free-text AI reasons, not the engine's brand checks
            match = BRAND_RE.search(str(item))
            if match:
                brands[match.group(1).strip()] += 1

    pending = Analysis.query.filter(
        Analysis.review_label.is_(None),
        db.or_(Analysis.reported_at.isnot(None), Analysis.score_risk.between(*BORDERLINE))).count()

    users_total = User.query.count()
    latest = Analysis.query.order_by(Analysis.created_at.desc()).limit(8).all()
    return ok({
        'analyses': {
            'total': total,
            'today': Analysis.query.filter(Analysis.created_at >= today).count(),
            'last_7_days': Analysis.query.filter(Analysis.created_at >= today - timedelta(days=6)).count(),
            'phishing': status_totals['phishing'],
            'suspicious': status_totals['suspicious'],
            'safe': status_totals['safe'],
            'phishing_rate': round(100 * status_totals['phishing'] / total, 1) if total else 0,
            'anonymous_share': round(100 * Analysis.query.filter(Analysis.user_id.is_(None)).count() / total, 1) if total else 0,
        },
        'series': [{'date': d, 'phishing': c['phishing'], 'suspicious': c['suspicious'], 'safe': c['safe']}
                   for d, c in days.items()],
        'top_domains': [{'domain': d, 'count': n} for d, n in domains.most_common(6)],
        'top_brands': [{'brand': b, 'count': n} for b, n in brands.most_common(6)],
        'review': {
            'pending': pending,
            'reported': Analysis.query.filter(Analysis.reported_at.isnot(None), Analysis.review_label.is_(None)).count(),
            'reviewed': Analysis.query.filter(Analysis.review_label.isnot(None)).count(),
        },
        'users': {
            'total': users_total,
            'new_7_days': User.query.filter(User.created_at >= today - timedelta(days=6)).count(),
            'suspended': User.query.filter_by(status='suspended').count(),
            'mfa_rate': round(100 * User.query.filter_by(mfa_active=True).count() / users_total, 1) if users_total else 0,
            'recent': [{
                'id': u.id, 'email': u.email, 'name': u.full_name, 'status': u.status or 'active',
                'is_admin': bool(u.is_admin), 'created_at': u.created_at.isoformat() if u.created_at else None,
                'last_login': u.last_login.isoformat() if u.last_login else None,
            } for u in User.query.order_by(User.last_login.desc().nullslast()).limit(6).all()],
        },
        'engine': _engine_info(),
        'latest': [{**_message(a), 'source': _source(a)} for a in latest],
    })


# --------------------------------------------------------- Review queue ----

def _queue_query(view: str):
    query = Analysis.query
    if view == 'reported':
        return query.filter(Analysis.reported_at.isnot(None), Analysis.review_label.is_(None))
    if view == 'borderline':
        return query.filter(Analysis.review_label.is_(None), Analysis.score_risk.between(*BORDERLINE))
    if view == 'reviewed':
        return query.filter(Analysis.review_label.isnot(None))
    return query.filter(Analysis.review_label.is_(None),
                        db.or_(Analysis.reported_at.isnot(None), Analysis.score_risk.between(*BORDERLINE)))


@admin_ops_bp.route('/review-queue', methods=['GET'])
@admin_required
def review_queue():
    view = request.args.get('view', 'pending')
    page = max(1, request.args.get('page', default=1, type=int))
    per_page = min(50, max(1, request.args.get('per_page', default=15, type=int)))
    query = _queue_query(view)
    total = query.count()
    order = (Analysis.reviewed_at.desc(),) if view == 'reviewed' else (
        Analysis.reported_at.desc().nullslast(), Analysis.created_at.desc())
    rows = query.order_by(*order).offset((page - 1) * per_page).limit(per_page).all()
    return ok({'items': [_queue_item(a) for a in rows], 'total': total, 'page': page, 'per_page': per_page})


@admin_ops_bp.route('/review-queue/<int:analysis_id>', methods=['GET'])
@admin_required
def review_item(analysis_id: int):
    analysis = db.session.get(Analysis, analysis_id)
    if not analysis:
        return err('NOT_FOUND', 'Analyse introuvable.', 404)
    return ok({**_analysis_detail(analysis), **_queue_item(analysis)})


@admin_ops_bp.route('/review-queue/<int:analysis_id>/decision', methods=['POST'])
@admin_required
def review_decision(analysis_id: int):
    analysis = db.session.get(Analysis, analysis_id)
    if not analysis:
        return err('NOT_FOUND', 'Analyse introuvable.', 404)
    data = request.get_json(silent=True) or {}
    label = data.get('label')
    if label == 'reset':
        analysis.review_label = analysis.reviewed_by = analysis.reviewed_at = analysis.review_note = None
    elif label in REVIEW_LABELS:
        analysis.review_label = label
        analysis.reviewed_by = current_user.id
        analysis.reviewed_at = datetime.utcnow()
        analysis.review_note = (data.get('note') or '')[:1000] or None
    else:
        return err('INVALID_LABEL', "Décision attendue : 'phishing', 'safe' ou 'reset'.")
    db.session.commit()
    return ok(_queue_item(analysis))


@admin_ops_bp.route('/review-queue/export', methods=['GET'])
@admin_required
def export_labels():
    """Admin-confirmed messages as a labelled CSV (text,label) for retraining."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['text', 'label', 'engine_score', 'reviewed_at'])
    for a in Analysis.query.filter(Analysis.review_label.isnot(None)).order_by(Analysis.reviewed_at).all():
        writer.writerow([a.text_source, 1 if a.review_label == 'phishing' else 0,
                         round(float(a.score_risk), 2), a.reviewed_at.isoformat() if a.reviewed_at else ''])
    return Response(buffer.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=phishguard_labels.csv'})


# ------------------------------------------------------------ Whitelist ----

def _serialize_domain(row: WhitelistDomain) -> dict:
    return {
        'id': row.id, 'domain': row.domain, 'institution': row.institution, 'category': row.category,
        'is_active': bool(row.is_active), 'created_at': row.created_at.isoformat() if row.created_at else None,
    }


def _clean_domain(value: str) -> str:
    value = (value or '').strip().lower()
    value = re.sub(r'^https?://', '', value).split('/')[0].removeprefix('www.')
    return value


@admin_ops_bp.route('/whitelist', methods=['GET'])
@admin_required
def list_whitelist():
    q = (request.args.get('q') or '').strip()
    query = WhitelistDomain.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(WhitelistDomain.domain.ilike(like), WhitelistDomain.institution.ilike(like)))
    rows = query.order_by(WhitelistDomain.category, WhitelistDomain.institution).all()
    return ok({'items': [_serialize_domain(r) for r in rows], 'total': len(rows)})


@admin_ops_bp.route('/whitelist', methods=['POST'])
@admin_required
def create_whitelist():
    data = request.get_json(silent=True) or {}
    domain = _clean_domain(data.get('domain'))
    institution = (data.get('institution') or '').strip()
    category = data.get('category') or 'other'
    if not DOMAIN_RE.match(domain):
        return err('INVALID_DOMAIN', 'Nom de domaine invalide (ex. mtn.cm).')
    if not institution:
        return err('INVALID_INSTITUTION', "Le nom de l'institution est requis.")
    if category not in WHITELIST_CATEGORIES:
        return err('INVALID_CATEGORY', 'Catégorie inconnue.')
    if WhitelistDomain.query.filter_by(domain=domain).first():
        return err('DUPLICATE', 'Ce domaine est déjà dans la liste blanche.', 409)
    row = WhitelistDomain(domain=domain, institution=institution[:255], category=category, is_active=True)
    db.session.add(row)
    db.session.commit()
    return ok(_serialize_domain(row), status=201)


@admin_ops_bp.route('/whitelist/<int:row_id>', methods=['PATCH'])
@admin_required
def update_whitelist(row_id: int):
    row = db.session.get(WhitelistDomain, row_id)
    if not row:
        return err('NOT_FOUND', 'Entrée introuvable.', 404)
    data = request.get_json(silent=True) or {}
    if 'is_active' in data:
        row.is_active = bool(data['is_active'])
    if 'institution' in data and (data['institution'] or '').strip():
        row.institution = data['institution'].strip()[:255]
    if 'category' in data:
        if data['category'] not in WHITELIST_CATEGORIES:
            return err('INVALID_CATEGORY', 'Catégorie inconnue.')
        row.category = data['category']
    db.session.commit()
    return ok(_serialize_domain(row))


@admin_ops_bp.route('/whitelist/<int:row_id>', methods=['DELETE'])
@admin_required
def delete_whitelist(row_id: int):
    row = db.session.get(WhitelistDomain, row_id)
    if not row:
        return err('NOT_FOUND', 'Entrée introuvable.', 404)
    db.session.delete(row)
    db.session.commit()
    return ok({'deleted': True})
