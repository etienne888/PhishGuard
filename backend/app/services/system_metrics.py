"""
Real system telemetry for the admin "System" view.

    * API traffic      - in-memory ring buffer filled by the after_request hook
                         (requests/min, error rate, p50/p95 latency, busiest endpoints)
    * Host             - CPU, memory, disk, process memory (psutil)
    * Database         - round-trip latency, size, connections, row counts
    * Detection engine - which components are loaded, pipeline duration p50/p95,
                         AI availability over the last analyses
"""
from __future__ import annotations

import os
import platform
import statistics
import threading
import time
from collections import Counter, deque
from datetime import datetime, timedelta

from sqlalchemy import text

from app import db

_requests: deque = deque(maxlen=5000)  # (timestamp, method, route, status, duration_ms)
_lock = threading.Lock()
STARTED_AT = time.time()


def record_request(method: str, route: str, status: int, duration_ms: int) -> None:
    with _lock:
        _requests.append((time.time(), method, route, status, duration_ms))


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = min(len(values) - 1, max(0, round(pct / 100 * (len(values) - 1))))
    return round(values[index], 1)


def traffic(minutes: int = 15) -> dict:
    cutoff = time.time() - minutes * 60
    with _lock:
        rows = [r for r in _requests if r[0] >= cutoff]
    durations = [r[4] for r in rows]
    errors = [r for r in rows if r[3] >= 500]
    client_errors = [r for r in rows if 400 <= r[3] < 500]
    # requests per minute, oldest first, for a sparkline
    per_minute = Counter(int((time.time() - r[0]) // 60) for r in rows)
    endpoints = Counter(f'{r[1]} {r[2]}' for r in rows)
    slow = Counter(f'{r[1]} {r[2]}' for r in rows if r[4] > 1000)
    return {
        'window_minutes': minutes,
        'requests': len(rows),
        'rpm': round(len(rows) / minutes, 1),
        'error_rate': round(len(errors) / len(rows) * 100, 2) if rows else 0,
        'client_error_rate': round(len(client_errors) / len(rows) * 100, 2) if rows else 0,
        'p50_ms': _percentile(durations, 50), 'p95_ms': _percentile(durations, 95),
        'sparkline': [per_minute.get(m, 0) for m in range(minutes - 1, -1, -1)],
        'top_endpoints': [{'endpoint': e, 'count': n} for e, n in endpoints.most_common(6)],
        'slow_endpoints': [{'endpoint': e, 'count': n} for e, n in slow.most_common(4)],
    }


def _fallback_host() -> dict:
    """Host figures from the standard library when psutil is not installed."""
    import shutil
    info: dict = {'available': True, 'partial': True, 'cpu_count': os.cpu_count()}
    disk = shutil.disk_usage(os.path.abspath(os.sep))
    info['disk_percent'] = round(disk.used / disk.total * 100, 1)
    info['disk_free_gb'] = round(disk.free / 1024 ** 3, 1)
    try:
        if os.name == 'nt':
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                            ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                            ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                            ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                            ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(MemoryStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            total, free = status.ullTotalPhys, status.ullAvailPhys

            def times():
                idle, kernel, user = (ctypes.c_ulonglong() for _ in range(3))
                ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))
                return idle.value, kernel.value + user.value  # kernel time includes idle time
            idle1, busy1 = times()
            time.sleep(0.2)
            idle2, busy2 = times()
            total_delta = busy2 - busy1
            info['cpu_percent'] = round((1 - (idle2 - idle1) / total_delta) * 100, 1) if total_delta else None
        else:
            meminfo = dict(line.split(':', 1) for line in open('/proc/meminfo'))
            total = int(meminfo['MemTotal'].split()[0]) * 1024
            free = int(meminfo['MemAvailable'].split()[0]) * 1024
            load1 = os.getloadavg()[0]
            info['cpu_percent'] = round(min(100.0, load1 / (os.cpu_count() or 1) * 100), 1)
        info['memory_percent'] = round((total - free) / total * 100, 1)
        info['memory_used_gb'] = round((total - free) / 1024 ** 3, 2)
        info['memory_total_gb'] = round(total / 1024 ** 3, 2)
    except Exception:  # best effort: disk figures are still useful
        pass
    return info


def host() -> dict:
    try:
        import psutil
    except ImportError:
        return {**_fallback_host(), 'python': platform.python_version(),
                'os': f'{platform.system()} {platform.release()}', 'threads': threading.active_count(),
                'uptime_seconds': round(time.time() - STARTED_AT)}
    process = psutil.Process(os.getpid())
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    return {
        'available': True,
        'cpu_percent': psutil.cpu_percent(interval=0.2),
        'cpu_count': psutil.cpu_count(),
        'memory_percent': memory.percent,
        'memory_used_gb': round(memory.used / 1024 ** 3, 2),
        'memory_total_gb': round(memory.total / 1024 ** 3, 2),
        'disk_percent': disk.percent,
        'disk_free_gb': round(disk.free / 1024 ** 3, 1),
        'process_memory_mb': round(process.memory_info().rss / 1024 ** 2, 1),
        'threads': process.num_threads(),
        'python': platform.python_version(),
        'os': f'{platform.system()} {platform.release()}',
        'uptime_seconds': round(time.time() - STARTED_AT),
    }


def database() -> dict:
    started = time.perf_counter()
    try:
        db.session.execute(text('SELECT 1'))
        latency = round((time.perf_counter() - started) * 1000, 1)
    except Exception as exc:
        db.session.rollback()
        return {'status': 'down', 'error': str(exc)[:200]}
    info: dict = {'status': 'up', 'latency_ms': latency}
    try:
        info['size_mb'] = round(db.session.execute(text('SELECT pg_database_size(current_database())')).scalar() / 1024 ** 2, 1)
        info['connections'] = db.session.execute(text(
            'SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()')).scalar()
        info['version'] = db.session.execute(text('SHOW server_version')).scalar()
    except Exception:
        db.session.rollback()
    counts = {}
    for table in ('users', 'analyses', 'incidents', 'security_events', 'whitelist_domains', 'blocked_domains'):
        try:
            counts[table] = db.session.execute(text(f'SELECT count(*) FROM {table}')).scalar()
        except Exception:
            db.session.rollback()
    info['tables'] = counts
    return info


def engine() -> dict:
    from app.models import Analysis
    from app.pipeline import _load_ml_model
    from app.pipeline.url_intel import get_xgb_model, xgb_enabled

    since = datetime.utcnow() - timedelta(hours=24)
    recent = Analysis.query.filter(Analysis.created_at >= since).order_by(Analysis.created_at.desc()).limit(300).all()
    durations = [a.duration_ms for a in recent if a.duration_ms]
    with_ai = 0
    for a in recent:
        raw = a.indicators if isinstance(a.indicators, dict) else {}
        if isinstance(a.indicators, str):
            import json
            try:
                raw = json.loads(a.indicators)
            except ValueError:
                raw = {}
        if isinstance(raw, dict) and raw.get('ai'):
            with_ai += 1
    hourly = Counter(int((datetime.utcnow() - a.created_at).total_seconds() // 3600) for a in recent)
    return {
        'components': {
            'text_model': _load_ml_model() is not None,
            'url_model': get_xgb_model() is not None and xgb_enabled(),
            'ai': bool(os.getenv('ANTHROPIC_API_KEY')),
            'smtp': bool(os.getenv('SMTP_HOST') and os.getenv('SMTP_PASSWORD')),
        },
        'analyses_24h': len(recent),
        'ai_coverage': round(with_ai / len(recent) * 100, 1) if recent else None,
        'pipeline_p50_ms': _percentile(durations, 50),
        'pipeline_p95_ms': _percentile(durations, 95),
        'pipeline_avg_ms': round(statistics.mean(durations)) if durations else None,
        'hourly': [hourly.get(h, 0) for h in range(23, -1, -1)],
    }


def experience() -> dict:
    """User-experience metrics: visitor -> account conversion, feedback, origins, connected mailboxes."""
    from sqlalchemy import func

    from app.models import Analysis, MailboxConnection
    from app.services import inbound_service, mailbox_service

    week = datetime.utcnow() - timedelta(days=7)
    month = datetime.utcnow() - timedelta(days=30)
    gated = Analysis.query.filter(Analysis.claim_expires_at.isnot(None), Analysis.created_at >= week)
    gated_total = gated.count()
    claimed = gated.filter(Analysis.claimed_at.isnot(None)).count()
    helpful = Analysis.query.filter(Analysis.feedback == 1, Analysis.feedback_at >= month).count()
    unhelpful = Analysis.query.filter(Analysis.feedback == -1, Analysis.feedback_at >= month).count()
    sources = dict(Analysis.query.with_entities(Analysis.source, func.count(Analysis.id))
                   .filter(Analysis.created_at >= week).group_by(Analysis.source).all())
    mailboxes = dict(MailboxConnection.query.with_entities(MailboxConnection.status, func.count(MailboxConnection.id))
                     .group_by(MailboxConnection.status).all())
    return {
        'visitor_scans_7d': gated_total,
        'visitor_claimed_7d': claimed,
        'conversion_rate': round(claimed / gated_total * 100, 1) if gated_total else None,
        'feedback_30d': {'helpful': helpful, 'not_helpful': unhelpful,
                         'helpful_rate': round(helpful / (helpful + unhelpful) * 100, 1) if helpful + unhelpful else None},
        'sources_7d': sources,
        'mailboxes': mailboxes,
        'providers': mailbox_service.configured(),
        'forwarding': inbound_service.configured(),
    }


def _safe(section) -> dict:
    """One failing section (e.g. a missing migration) must not hide the rest of the page."""
    try:
        return section()
    except Exception as exc:
        db.session.rollback()
        return {'error': type(exc).__name__}


def snapshot() -> dict:
    from app.services import scheduler

    data = {'generated_at': datetime.utcnow().isoformat(), 'traffic': traffic(), 'host': _safe(host),
            'database': database(), 'engine': _safe(engine), 'experience': _safe(experience),
            'jobs': scheduler.status()}
    data['engine'].setdefault('components', {'text_model': False, 'url_model': False, 'ai': False, 'smtp': False})
    for key in ('analyses_24h', 'ai_coverage', 'pipeline_p50_ms', 'pipeline_p95_ms', 'pipeline_avg_ms'):
        data['engine'].setdefault(key, None)
    data['engine'].setdefault('hourly', [])
    # One overall status, worst component wins
    problems = []
    if data['database'].get('status') != 'up':
        problems.append('database')
    if data['traffic']['error_rate'] > 5:
        problems.append('errors')
    if (data['host'].get('memory_percent') or 0) > 90 or (data['host'].get('disk_percent') or 0) > 95:
        problems.append('resources')
    if not data['engine']['components']['ai']:
        problems.append('ai')
    if any(not job.get('ok', True) for job in data['jobs'].values()):
        problems.append('jobs')
    data['status'] = 'down' if 'database' in problems else 'degraded' if problems else 'healthy'
    data['problems'] = problems
    return data
