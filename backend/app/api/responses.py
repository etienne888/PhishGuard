from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from flask import g, jsonify


def request_id() -> str:
    return getattr(g, 'request_id', str(uuid4()))


def duration_ms() -> int:
    started_at = getattr(g, 'request_started_at', None)
    if started_at is None:
        return 0
    return round((perf_counter() - started_at) * 1000)


def ok(data, meta=None, status: int = 200):
    return jsonify({
        'data': data,
        'meta': {
            'request_id': request_id(),
            'duration_ms': duration_ms(),
            **(meta or {}),
        },
    }), status


def err(code: str, message: str, status: int = 400, detail=None):
    return jsonify({
        'error': {
            'code': code,
            'message': message,
            'detail': detail,
        },
    }), status
