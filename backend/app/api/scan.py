# backend/app/api/scan.py
"""v2 scan endpoint: pasted text (JSON) or .eml upload (multipart)."""

import json

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app import db
from app.models import Analysis
from app.pipeline import ParseError, run_pipeline

scan_bp = Blueprint('scan', __name__)

MAX_EML_BYTES = 5 * 1024 * 1024


@scan_bp.route('/scan', methods=['POST'])
def scan():
    try:
        if 'file' in request.files:
            upload = request.files['file']
            if not (upload.filename or '').lower().endswith('.eml'):
                return jsonify({'error': {'code': 'invalid_file', 'message': 'Seuls les fichiers .eml sont acceptés.'}}), 400
            raw = upload.read(MAX_EML_BYTES + 1)
            if len(raw) > MAX_EML_BYTES:
                return jsonify({'error': {'code': 'file_too_large', 'message': 'Fichier trop volumineux (5 Mo maximum).'}}), 400
            result = run_pipeline(raw_eml=raw, source='web')
        else:
            data = request.get_json(silent=True) or {}
            result = run_pipeline(text=data.get('text', ''), source=data.get('source', 'web'))
    except ParseError as exc:
        return jsonify({'error': {'code': 'invalid_input', 'message': str(exc)}}), 400

    msg = result['message']
    analysis = Analysis(
        user_id=current_user.id if current_user.is_authenticated else None,
        text_source=(request.get_json(silent=True) or {}).get('text', '')[:1000] or (msg.get('subject') or '.eml'),
        score_risk=result['score'],
        verdict=result['verdict'],
        indicators=json.dumps(result['evidence']),
        email_from=(msg.get('sender') or '')[:255] or None,
        subject=(msg.get('subject') or '')[:255] or None,
        urls=[u['url'] for u in result['urls']],
    )
    db.session.add(analysis)
    db.session.commit()
    result['analysis_id'] = analysis.id
    return jsonify(result), 200
