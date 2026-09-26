"""
Background jobs (one daemon thread, no extra dependency).

    every MAILBOX_SYNC_MINUTES (5)   connected mailboxes: scan new emails
    every 2 minutes                  forwarded emails (IMAP inbox), when configured
    every 15 minutes                 incident correlation
    every hour                       OpenPhish feed refresh
    every 12 hours                   allowlist domain health (DNS/TLS)

Started on the first request served (so with the Flask reloader only the serving
process runs it and jobs never run twice); SCHEDULER_ENABLED=false turns it off.
Each job runs in an app context and can never stop the loop.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime

log = logging.getLogger(__name__)

_started = False
_status: dict[str, dict] = {}


def _jobs():
    from app.services import inbound_service, mailbox_service

    mailbox_every = int(os.getenv('MAILBOX_SYNC_MINUTES', '5'))

    def mailboxes():
        return mailbox_service.sync_all_due(mailbox_every)

    def forwarded():
        return inbound_service.poll()

    def correlation():
        from app.services.correlation_service import correlate
        return correlate()

    def feed():
        from app.services.threat_feed import load
        return bool(load(force=True))

    def allowlist_health():
        from app import db
        from app.models import WhitelistDomain
        from app.services.domain_health import check_many
        rows = WhitelistDomain.query.all()
        results = check_many([r.domain for r in rows])
        now = datetime.utcnow()
        for r in rows:
            r.health, r.last_checked_at = results.get(r.domain), now
        db.session.commit()
        return len(rows)

    return [
        ('mailboxes', mailbox_every * 60, mailboxes),
        ('forwarded_emails', 120, forwarded),
        ('correlation', 15 * 60, correlation),
        ('threat_feed', 3600, feed),
        ('allowlist_health', 12 * 3600, allowlist_health),
    ]


def status() -> dict[str, dict]:
    """Last run of each job, for the admin System page."""
    return {name: dict(info) for name, info in _status.items()}


def _loop(app):
    jobs = _jobs()
    next_run = {name: time.time() + 30 for name, _, _ in jobs}  # let the server start first
    while True:
        for name, every, job in jobs:
            if time.time() < next_run[name]:
                continue
            next_run[name] = time.time() + every
            started = time.perf_counter()
            with app.app_context():
                try:
                    result = job()
                    _status[name] = {'last_run': datetime.utcnow().isoformat(), 'ok': True,
                                     'result': result if isinstance(result, (int, bool)) else None,
                                     'duration_ms': round((time.perf_counter() - started) * 1000),
                                     'every_seconds': every}
                except Exception as exc:
                    log.exception('Background job %s failed', name)
                    from app import db
                    db.session.rollback()
                    _status[name] = {'last_run': datetime.utcnow().isoformat(), 'ok': False,
                                     'error': type(exc).__name__, 'every_seconds': every}
                finally:
                    from app import db
                    db.session.remove()
        time.sleep(10)


def start(app) -> None:
    global _started
    if _started or os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'false' or app.testing:
        return
    _started = True
    threading.Thread(target=_loop, args=(app,), name='phishguard-scheduler', daemon=True).start()
    log.info('Background scheduler started')
