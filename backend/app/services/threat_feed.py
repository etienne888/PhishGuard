"""
External threat intelligence: the OpenPhish community feed (free, no key).

The feed (~500 live phishing URLs, refreshed every 12 h upstream) is downloaded
at most once an hour and cached in instance/openphish.txt. The platform's own
indicators are matched against it so analysts see which domains the wider
community has already confirmed.
"""
from __future__ import annotations

import logging
import os
import time

import requests
from flask import current_app

from app.pipeline.sender import registered_domain
from app.services.indicators import host_of

logger = logging.getLogger(__name__)

FEED_URL = 'https://openphish.com/feed.txt'
TTL = 3600
RETRY_AFTER = 600  # after a failed download, wait 10 min before trying again
_last_failure = 0.0


def _path() -> str:
    os.makedirs(current_app.instance_path, exist_ok=True)
    return os.path.join(current_app.instance_path, 'openphish.txt')


def load(force: bool = False) -> dict:
    """Return {'urls': [...], 'domains': set, 'fetched_at': epoch|None, 'ok': bool}."""
    global _last_failure
    path = _path()
    fresh = os.path.exists(path) and time.time() - os.path.getmtime(path) < TTL
    backing_off = time.time() - _last_failure < RETRY_AFTER
    if force or (not fresh and not backing_off):
        try:
            response = requests.get(FEED_URL, timeout=12, headers={'User-Agent': 'PhishGuard-AI (academic)'})
            response.raise_for_status()
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(response.text)
        except requests.RequestException as exc:
            _last_failure = time.time()
            logger.info('OpenPhish feed unavailable: %s', exc)
    if not os.path.exists(path):
        return {'urls': [], 'domains': set(), 'fetched_at': None, 'ok': False}
    with open(path, encoding='utf-8') as fh:
        urls = [line.strip() for line in fh if line.strip()]
    domains = {registered_domain(host_of(u)) for u in urls if host_of(u)}
    return {'urls': urls, 'domains': domains, 'fetched_at': os.path.getmtime(path), 'ok': True}
