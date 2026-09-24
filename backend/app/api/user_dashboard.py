from __future__ import annotations

import json
from datetime import datetime, timedelta

from flask import Blueprint, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.api.responses import err, ok
from app.models import Analysis

user_dashboard_bp = Blueprint('user_dashboard', __name__)


def _analysis_status(verdict: str) -> str:
    normalized = (verdict or '').lower()
    if normalized in {'phishing', 'critical', 'high'}:
        return 'phishing'
    if normalized in {'suspicious', 'medium'}:
        return 'suspicious'
    return 'safe'


def _details(analysis: Analysis) -> dict:
    """
    Stored analysis details. v2 scans store a dict
    ({evidence, level, signals, weights, overrides, ai, recommendation});
    older rows store a bare list of indicator strings.
    """
    raw = analysis.indicators
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = []
    if isinstance(raw, dict):
        return raw
    return {'evidence': raw if isinstance(raw, list) else []}


def _indicators(analysis: Analysis) -> list[object]:
    return _details(analysis).get('evidence', [])


def _message(analysis: Analysis) -> dict:
    status = _analysis_status(analysis.verdict)
    return {
        'id': analysis.id,
        'sender': analysis.email_from or 'Expéditeur inconnu',
        'subject': analysis.subject or 'Analyse de message',
        'received_at': analysis.created_at.isoformat() if analysis.created_at else None,
        'status': status,
        'score': round(float(analysis.score_risk), 2),
        'threat_type': 'Phishing' if status == 'phishing' else 'Message suspect' if status == 'suspicious' else 'Aucune menace',
        'preview': analysis.text_source[:160],
        'reported_at': None,
    }


def _user_analyses():
    return Analysis.query.filter_by(user_id=current_user.id)


@user_dashboard_bp.route('/dashboard/overview', methods=['GET'])
@login_required
def dashboard_overview():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today = _user_analyses().filter(Analysis.created_at >= today_start)
    analyses = today.all()
    status_counts = {'safe': 0, 'suspicious': 0, 'phishing': 0}
    for analysis in analyses:
        status_counts[_analysis_status(analysis.verdict)] += 1

    average_risk = sum(float(analysis.score_risk) for analysis in analyses) / len(analyses) if analyses else 0
    last_analysis = _user_analyses().order_by(Analysis.created_at.desc()).first()
    return ok({
        'protection_status': 'active',
        'last_sync_at': last_analysis.created_at.isoformat() if last_analysis and last_analysis.created_at else None,
        'vigilance_score': round(max(0, 100 - average_risk)),
        'emails_analyzed_today': len(analyses),
        'safe_today': status_counts['safe'],
        'suspicious_today': status_counts['suspicious'],
        'threats_today': status_counts['phishing'],
        'quarantined_today': status_counts['phishing'],
    })


@user_dashboard_bp.route('/dashboard/recent-messages', methods=['GET'])
@login_required
def recent_messages():
    limit = min(max(request.args.get('limit', 20, type=int), 1), 100)
    query = _user_analyses().order_by(Analysis.created_at.desc())
    total = query.count()
    return ok({'items': [_message(analysis) for analysis in query.limit(limit).all()], 'total': total})


@user_dashboard_bp.route('/dashboard/activity', methods=['GET'])
@login_required
def dashboard_activity():
    limit = min(max(request.args.get('limit', 10, type=int), 1), 100)
    events: list[dict] = []
    for analysis in _user_analyses().order_by(Analysis.created_at.desc()).limit(limit).all():
        status = _analysis_status(analysis.verdict)
        events.append({
            'id': analysis.id,
            'type': 'threat' if status == 'phishing' else 'analysis',
            'action': 'Menace détectée' if status == 'phishing' else 'Analyse terminée',
            'details': analysis.subject or analysis.email_from or 'Message analysé',
            'occurred_at': analysis.created_at.isoformat() if analysis.created_at else None,
        })
    return ok({'items': events})


@user_dashboard_bp.route('/dashboard/timeline', methods=['GET'])
@login_required
def dashboard_timeline():
    ranges = {'today': 1, '7d': 7, '30d': 30, '90d': 90}
    selected_range = request.args.get('range', 'today')
    if selected_range not in ranges:
        return err('INVALID_RANGE', 'Plage de temps invalide.')

    since = datetime.utcnow() - timedelta(days=ranges[selected_range])
    items = []
    for analysis in _user_analyses().filter(Analysis.created_at >= since).order_by(Analysis.created_at.desc()).limit(100).all():
        status = _analysis_status(analysis.verdict)
        items.append({
            'id': analysis.id,
            'time': analysis.created_at.strftime('%H:%M') if analysis.created_at else '',
            'title': analysis.subject or 'Analyse de message',
            'risk': round(float(analysis.score_risk)),
            'action': 'Bloqué' if status == 'phishing' else 'Classé',
            'tone': 'critical' if status == 'phishing' else 'high' if status == 'suspicious' else 'safe',
        })
    return ok({'items': items})


@user_dashboard_bp.route('/dashboard/score-breakdown', methods=['GET'])
@login_required
def score_breakdown():
    analyses = _user_analyses().order_by(Analysis.created_at.desc()).limit(100).all()
    if not analyses:
        return ok({'score': None, 'reasons': []})

    score = round(max(0, 100 - (sum(float(analysis.score_risk) for analysis in analyses) / len(analyses))))
    reasons = []
    for analysis in analyses[:10]:
        status = _analysis_status(analysis.verdict)
        reasons.append({
            'label': analysis.subject or analysis.email_from or 'Analyse de message',
            'delta': -round(float(analysis.score_risk) / 10) if status != 'safe' else 1,
        })
    return ok({'score': score, 'reasons': reasons})


@user_dashboard_bp.route('/messages/<int:analysis_id>/report', methods=['POST'])
@login_required
def report_message(analysis_id: int):
    analysis = _user_analyses().filter_by(id=analysis_id).first()
    if not analysis:
        return err('NOT_FOUND', 'Message introuvable.', 404)
    return ok({'id': analysis.id, 'reported_at': datetime.utcnow().isoformat()})


@user_dashboard_bp.route('/dashboard/security-check', methods=['POST'])
@login_required
def security_check():
    return ok({
        'mfa_active': bool(current_user.mfa_active),
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
        'account_locked': bool(current_user.locked_until and current_user.locked_until > datetime.utcnow()),
    })


def _analysis_detail(analysis: Analysis) -> dict:
    details = _details(analysis)
    return {
        **_message(analysis),
        'text': analysis.text_source,
        'urls': analysis.urls or [],
        'evidence': details.get('evidence', []),
        'level': details.get('level'),
        'signals': details.get('signals'),
        'weights': details.get('weights'),
        'overrides': details.get('overrides', []),
        'ai': details.get('ai'),
        'recommendation': details.get('recommendation'),
    }


@user_dashboard_bp.route('/analyses', methods=['GET'])
@login_required
def list_analyses():
    """Full history with search, verdict filter and pagination."""
    page = max(1, request.args.get('page', default=1, type=int))
    per_page = min(50, max(1, request.args.get('per_page', default=10, type=int)))
    status = request.args.get('status')
    q = (request.args.get('q') or '').strip()

    query = _user_analyses()
    if status == 'phishing':
        query = query.filter(Analysis.verdict.in_(['phishing', 'Critical', 'High']))
    elif status == 'suspicious':
        query = query.filter(Analysis.verdict.in_(['suspicious', 'Medium']))
    elif status == 'safe':
        query = query.filter(Analysis.verdict.notin_(['phishing', 'Critical', 'High', 'suspicious', 'Medium']))
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Analysis.text_source.ilike(like), Analysis.subject.ilike(like),
                                    Analysis.email_from.ilike(like)))

    total = query.count()
    rows = query.order_by(Analysis.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return ok({'items': [_message(a) for a in rows], 'total': total, 'page': page, 'per_page': per_page})


@user_dashboard_bp.route('/analyses/<int:analysis_id>', methods=['GET'])
@login_required
def get_analysis(analysis_id: int):
    analysis = _user_analyses().filter_by(id=analysis_id).first()
    if not analysis:
        return err('NOT_FOUND', 'Analyse introuvable.', 404)
    return ok(_analysis_detail(analysis))


@user_dashboard_bp.route('/notifications', methods=['GET'])
@login_required
def notifications():
    """
    Notifications derived from the user's analyses (threats and suspicious
    messages from the last 30 days) plus a welcome/learning tip.
    Read state is kept per browser on the client.
    """
    since = datetime.utcnow() - timedelta(days=30)
    rows = (_user_analyses()
            .filter(Analysis.created_at >= since)
            .order_by(Analysis.created_at.desc()).limit(30).all())
    items = []
    for a in rows:
        status = _analysis_status(a.verdict)
        if status == 'safe':
            continue
        details = _details(a)
        items.append({
            'id': f'analysis-{a.id}',
            'analysis_id': a.id,
            'type': 'threat' if status == 'phishing' else 'warning',
            'title': 'Menace détectée' if status == 'phishing' else 'Message suspect',
            'body': (details.get('ai') or {}).get('recommendation') or details.get('recommendation')
                    or f"Score de risque {round(float(a.score_risk))}/100 : {a.text_source[:90]}",
            'created_at': a.created_at.isoformat() if a.created_at else None,
        })
    if not current_user.mfa_active:
        items.append({
            'id': 'tip-mfa',
            'analysis_id': None,
            'type': 'tip',
            'title': 'Protégez votre compte',
            'body': "Activez la double authentification (code OTP) dans Paramètres › Sécurité.",
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        })
    return ok({'items': items})


@user_dashboard_bp.route('/messages/<int:analysis_id>/explanation', methods=['GET'])
@login_required
def message_explanation(analysis_id: int):
    analysis = _user_analyses().filter_by(id=analysis_id).first()
    if not analysis:
        return err('NOT_FOUND', 'Message introuvable.', 404)

    indicators = _indicators(analysis)
    return ok({
        'analysis_id': analysis.id,
        'explanation': '',
        'indicators': indicators,
    })
