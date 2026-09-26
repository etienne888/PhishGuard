from __future__ import annotations

import json
from datetime import datetime, timedelta

from flask import Blueprint, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.api.responses import err, ok
from app.models import Analysis
from app.pipeline.i18n import request_lang, tr

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
        'sender': analysis.email_from or tr(request_lang(), 'sender.unknown'),
        'subject': analysis.subject or 'Analyse de message',
        'received_at': analysis.created_at.isoformat() if analysis.created_at else None,
        'status': status,
        'score': round(float(analysis.score_risk), 2),
        'threat_type': 'Phishing' if status == 'phishing' else 'Message suspect' if status == 'suspicious' else 'Aucune menace',
        'preview': analysis.text_source[:160],
        'reported_at': analysis.reported_at.isoformat() if analysis.reported_at else None,
        # Admin decision, so users can follow what happened to their report
        'review_label': analysis.review_label,
        'origin': analysis.source or 'web',  # web | mailbox | forward | share
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
            'title': analysis.subject or tr(request_lang(), 'message.default_title'),
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
            'label': analysis.subject or analysis.email_from or tr(request_lang(), 'message.default_title'),
            'delta': -round(float(analysis.score_risk) / 10) if status != 'safe' else 1,
        })
    return ok({'score': score, 'reasons': reasons})


@user_dashboard_bp.route('/messages/<int:analysis_id>/report', methods=['POST'])
@login_required
def report_message(analysis_id: int):
    analysis = _user_analyses().filter_by(id=analysis_id).first()
    if not analysis:
        return err('NOT_FOUND', 'Message introuvable.', 404)
    if analysis.reported_at is None:
        analysis.reported_at = datetime.utcnow()
        analysis.report_note = ((request.get_json(silent=True) or {}).get('note') or '')[:1000] or None
        db.session.commit()
        # The engine pre-sorts the report; confident cases may be closed automatically
        from app.services.triage_service import triage
        triage(analysis)
    return ok({'id': analysis.id, 'reported_at': analysis.reported_at.isoformat()})


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
    source = request.args.get('source')
    if source in ('web', 'mailbox', 'forward', 'share'):
        query = query.filter(Analysis.source == source)
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
    lang = request_lang()
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
            'title': (tr(lang, 'notif.mailbox_threat', mailbox=a.email_from or '')
                      if a.source == 'mailbox' and status == 'phishing'
                      else tr(lang, 'notif.threat' if status == 'phishing' else 'notif.suspicious')),
            'body': (details.get('ai') or {}).get('recommendation') or details.get('recommendation')
                    or tr(lang, 'notif.score', score=round(float(a.score_risk)), text=a.text_source[:90]),
            'created_at': a.created_at.isoformat() if a.created_at else None,
        })
    # Outcome of the user's own reports (admin or automatic review)
    reviewed = (_user_analyses().filter(Analysis.reported_at.isnot(None), Analysis.reviewed_at.isnot(None),
                                        Analysis.reviewed_at >= since)
                .order_by(Analysis.reviewed_at.desc()).limit(10).all())
    for a in reviewed:
        items.append({
            'id': f'review-{a.id}',
            'analysis_id': a.id,
            'type': 'success',
            'title': tr(lang, 'notif.review_phishing' if a.review_label == 'phishing' else 'notif.review_safe'),
            'body': tr(lang, 'notif.review_body', text=a.text_source[:90]),
            'created_at': a.reviewed_at.isoformat(),
        })
    items.sort(key=lambda item: item['created_at'] or '', reverse=True)
    if not current_user.mfa_active:
        items.append({
            'id': 'tip-mfa',
            'analysis_id': None,
            'type': 'tip',
            'title': tr(lang, 'notif.mfa_title'),
            'body': tr(lang, 'notif.mfa_body'),
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


# ---------- privacy: delete history ----------

@user_dashboard_bp.route('/analyses/<int:analysis_id>', methods=['DELETE'])
@login_required
def delete_analysis(analysis_id: int):
    deleted = _user_analyses().filter_by(id=analysis_id).delete()
    db.session.commit()
    if not deleted:
        return err('NOT_FOUND', tr(request_lang(), 'error.not_found'), 404)
    return ok({'deleted': 1})


@user_dashboard_bp.route('/analyses', methods=['DELETE'])
@login_required
def delete_history():
    """One-click deletion of the user's whole analysis history."""
    from app.services import audit_service
    count = _user_analyses().delete(synchronize_session=False)
    db.session.commit()
    audit_service.record('privacy.history_deleted', user_id=current_user.id, details={'analyses': count})
    return ok({'deleted': count})


# ---------- monthly summary, awareness quiz, onboarding ----------

LEVELS = [(0, 'novice'), (50, 'vigilant'), (150, 'guardian'), (400, 'expert'), (800, 'master')]


def _level(xp: int) -> dict:
    current = [lv for lv in LEVELS if xp >= lv[0]][-1]
    following = next((lv for lv in LEVELS if lv[0] > xp), None)
    return {'key': current[1], 'xp': xp, 'floor': current[0], 'next': following[0] if following else None}


@user_dashboard_bp.route('/summary', methods=['GET'])
@login_required
def monthly_summary():
    """"This month": scans, threats avoided, where they came from, most imitated brand."""
    now = datetime.utcnow()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_start = (start - timedelta(days=1)).replace(day=1)
    rows = _user_analyses().filter(Analysis.created_at >= start).all()
    prev_rows = _user_analyses().filter(Analysis.created_at >= prev_start, Analysis.created_at < start).count()
    threats = [a for a in rows if _analysis_status(a.verdict) == 'phishing']
    suspicious = [a for a in rows if _analysis_status(a.verdict) == 'suspicious']
    brands: dict[str, int] = {}
    for a in threats + suspicious:
        brand = _details(a).get('brand')
        if brand:
            brands[brand] = brands.get(brand, 0) + 1
    sources: dict[str, int] = {}
    for a in rows:
        sources[a.source or 'web'] = sources.get(a.source or 'web', 0) + 1
    return ok({
        'month': start.strftime('%Y-%m'),
        'scans': len(rows),
        'scans_previous_month': prev_rows,
        'threats_avoided': len(threats),
        'suspicious': len(suspicious),
        'safe': len(rows) - len(threats) - len(suspicious),
        'reports': sum(1 for a in rows if a.reported_at),
        'top_brand': max(brands, key=brands.get) if brands else None,
        'sources': sources,
        'quiz': {'answered': current_user.quiz_answered or 0, 'correct': current_user.quiz_correct or 0,
                 'level': _level(current_user.quiz_xp or 0)},
    })


@user_dashboard_bp.route('/quiz/answer', methods=['POST'])
@login_required
def quiz_answer():
    """Record one "real or fake?" answer: +10 XP when correct, +2 for trying."""
    correct = bool((request.get_json(silent=True) or {}).get('correct'))
    current_user.quiz_answered = (current_user.quiz_answered or 0) + 1
    current_user.quiz_correct = (current_user.quiz_correct or 0) + (1 if correct else 0)
    current_user.quiz_xp = (current_user.quiz_xp or 0) + (10 if correct else 2)
    db.session.commit()
    return ok({'answered': current_user.quiz_answered, 'correct': current_user.quiz_correct,
               'level': _level(current_user.quiz_xp)})


@user_dashboard_bp.route('/onboarded', methods=['POST'])
@login_required
def onboarded():
    if current_user.onboarded_at is None:
        current_user.onboarded_at = datetime.utcnow()
        db.session.commit()
    return ok({'onboarded': True})


@user_dashboard_bp.route('/origins', methods=['GET'])
@login_required
def my_threat_origins():
    """"Where do my threats come from?": approximate origin of the user's dangerous emails (no IPs)."""
    from app.services.email_origin import public_view
    since = datetime.utcnow() - timedelta(days=request.args.get('days', default=90, type=int))
    points, hidden = {}, 0
    for a in (_user_analyses().filter(Analysis.created_at >= since, Analysis.verdict.in_(('phishing', 'suspicious')))
              .order_by(Analysis.created_at.desc()).limit(500)):
        view = public_view(_details(a).get('origin'))
        if not view:
            continue
        if view['precision'] == 'hidden' or view['lat'] is None:
            hidden += 1
            continue
        key = (round(view['lat'], 1), round(view['lon'], 1))
        p = points.setdefault(key, {'lat': key[0], 'lon': key[1], 'city': view['city'], 'country': view['country'],
                                    'country_code': view['country_code'], 'count': 0, 'isp': view['isp'],
                                    'accuracy_km': view['accuracy_km'], 'analyses': []})
        p['count'] += 1
        if len(p['analyses']) < 10:
            p['analyses'].append({'id': a.id, 'subject': a.subject, 'verdict': a.verdict,
                                  'created_at': a.created_at.isoformat() if a.created_at else None})
    return ok({'points': list(points.values()), 'hidden': hidden})
