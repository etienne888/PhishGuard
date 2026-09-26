"""v2 scan endpoint: pasted text (JSON) or .eml upload (multipart).

Visitors can submit a message: it is analysed straight away, but the result is
only returned after sign-in (POST /scan/claim with the claim token). Signed-in
users get the result immediately.
"""

import time
from collections import defaultdict, deque

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.api.responses import err, ok
from app.models import Analysis
from app.pipeline import ParseError, normalize_lang, run_pipeline
from app.pipeline.i18n import request_lang, tr
from app.services import email_origin, scan_service
from app.services.client_info import client_ip

scan_bp = Blueprint('scan', __name__)

MAX_EML_BYTES = 5 * 1024 * 1024
SOURCES = {'web', 'share'}

# Visitors: at most VISITOR_LIMIT scans per IP per hour (in memory, per process)
VISITOR_LIMIT = 15
_visitor_hits: dict[str, deque] = defaultdict(deque)


def _visitor_rate_limited(ip: str) -> bool:
    now = time.time()
    hits = _visitor_hits[ip]
    while hits and now - hits[0] > 3600:
        hits.popleft()
    if len(hits) >= VISITOR_LIMIT:
        return True
    hits.append(now)
    return False


@scan_bp.route('/scan', methods=['POST'])
def scan():
    # Explanations follow the interface language: `lang` field, else Accept-Language
    data = request.get_json(silent=True) or {}
    lang = normalize_lang(data.get('lang') or request.form.get('lang') or request.headers.get('Accept-Language'))
    signed_in = current_user.is_authenticated
    if not signed_in and _visitor_rate_limited(client_ip() or 'unknown'):
        return jsonify({'error': {'code': 'RATE_LIMITED', 'message': tr(lang, 'error.rate_limited')}}), 429
    source = (data.get('source') or request.form.get('source') or 'web')
    source = source if source in SOURCES else 'web'
    text = ''
    try:
        if 'file' in request.files:
            upload = request.files['file']
            if not (upload.filename or '').lower().endswith('.eml'):
                return jsonify({'error': {'code': 'invalid_file', 'message': tr(lang, 'error.eml_only')}}), 400
            raw = upload.read(MAX_EML_BYTES + 1)
            if len(raw) > MAX_EML_BYTES:
                return jsonify({'error': {'code': 'file_too_large', 'message': tr(lang, 'error.too_large')}}), 400
            result = run_pipeline(raw_eml=raw, source='web', lang=lang)
        else:
            text = data.get('text', '')
            result = run_pipeline(text=text, source=source, lang=lang)
    except ParseError as exc:
        return jsonify({'error': {'code': 'invalid_input', 'message': exc.message(lang)}}), 400

    scan_service.finalize(result)
    analysis = scan_service.save(result, user_id=current_user.id if signed_in else None, source=source, text=text)

    if not signed_in:
        # Analysed, but the result is only revealed after sign-in
        token = scan_service.issue_claim(analysis)
        return jsonify({
            'gated': True,
            'claim_token': token,
            'checks': len(result.get('signals') or {}) + len(result.get('url_details') or []),
            'duration_ms': result.get('duration_ms'),
            'safety_tip': tr(lang, 'gated.tip'),
        }), 200

    result['analysis_id'] = analysis.id
    result['official'] = scan_service.official_contact(result.get('brand'))
    result['origin'] = email_origin.public_view(result.get('origin'))  # full report is admin-only
    result['text'] = analysis.text_source
    return jsonify(result), 200


@scan_bp.route('/scan/claim', methods=['POST'])
@login_required
def claim():
    """Attach a visitor scan to the signed-in account and return its result."""
    token = ((request.get_json(silent=True) or {}).get('claim_token') or '').strip()
    analysis = scan_service.claim(token, current_user.id)
    if analysis is None:
        return err('CLAIM_INVALID', tr(request_lang(), 'error.claim_invalid'), 404)
    return ok(scan_service.to_result(analysis))


@scan_bp.route('/scan/<int:analysis_id>', methods=['GET'])
@login_required
def get_result(analysis_id: int):
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    if analysis is None:
        return err('NOT_FOUND', tr(request_lang(), 'error.not_found'), 404)
    return ok(scan_service.to_result(analysis))


@scan_bp.route('/scan/<int:analysis_id>/feedback', methods=['POST'])
@login_required
def feedback(analysis_id: int):
    """"Was this helpful?" (1 / -1) with an optional comment; feeds the admin UX metrics."""
    from datetime import datetime
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    if analysis is None:
        return err('NOT_FOUND', tr(request_lang(), 'error.not_found'), 404)
    body = request.get_json(silent=True) or {}
    value = body.get('value')
    if value not in (1, -1):
        return err('VALIDATION_ERROR', 'value must be 1 or -1', 400)
    analysis.feedback = value
    analysis.feedback_note = (body.get('note') or '')[:1000] or None
    analysis.feedback_at = datetime.utcnow()
    db.session.commit()
    return ok({'id': analysis.id, 'feedback': value})
