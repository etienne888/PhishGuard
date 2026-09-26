"""
Indicators of compromise (IOCs) extracted from stored analyses.

One place that knows how to turn an analysis into indicators, shared by the
incident correlation engine, the threat-intelligence view and the command centre.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from app.models import Analysis
from app.pipeline.sender import registered_domain

# Brand names inside the engine's evidence lines, in either language (see pipeline/i18n.py)
BRAND_RE = re.compile(r"(?:imite|nom de|imitates|name of) ([A-ZÀ-Ý][\w'’À-ÿ\- ]+?)(?: sans| without| \(|\s*:|$)")


def details(analysis: Analysis) -> dict:
    raw = analysis.indicators
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    return raw if isinstance(raw, dict) else {'evidence': raw if isinstance(raw, list) else []}


def host_of(url: str) -> str:
    return (urlparse(url if '://' in url else f'http://{url}').hostname or '').lower().strip('.')


def brands(analysis: Analysis) -> set[str]:
    found = set()
    for item in details(analysis).get('evidence', []):
        text = str(item)
        if text.startswith(('IA :', 'AI:')):
            continue  # free-text AI reasons, not the engine's brand checks
        match = BRAND_RE.search(text)
        if match:
            found.add(match.group(1).strip())
    return found


def extract(analysis: Analysis, whitelist: dict | None = None) -> list[tuple[str, str]]:
    """[(type, value)] for one analysis: 'domain' (registered domain of each link),
    'url', 'sender' (sender domain) and 'brand' (impersonated institution)."""
    whitelist = whitelist or {}
    out: list[tuple[str, str]] = []
    for url in analysis.urls or []:
        host = host_of(url)
        if not host:
            continue
        domain = registered_domain(host)
        if domain in whitelist or host in whitelist:
            continue  # links to the real institution are not indicators
        out.append(('domain', domain))
        out.append(('url', url[:500]))
    if analysis.email_from and '@' in analysis.email_from:
        sender_domain = analysis.email_from.rsplit('@', 1)[-1].strip('> ').lower()
        if sender_domain and registered_domain(sender_domain) not in whitelist:
            out.append(('sender', sender_domain))
    out.extend(('brand', b) for b in brands(analysis))
    return out
