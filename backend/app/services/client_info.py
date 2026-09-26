"""
Who is on the other end of the request: real client IP, device, approximate location.

The Vite dev server (and any reverse proxy) forwards the browser's address in
X-Forwarded-For; it is only trusted when the direct peer is a local proxy, so a
client cannot spoof its IP by sending the header itself.
"""
from __future__ import annotations

import ipaddress
import logging
import re

import requests
from flask import has_request_context, request

logger = logging.getLogger(__name__)

TRUSTED_PROXIES = {'127.0.0.1', '::1'}
GEO_URL = 'http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,isp,org,as,proxy,hosting,mobile'
_geo_cache: dict[str, dict] = {}


def client_ip() -> str | None:
    if not has_request_context():
        return None
    peer = request.remote_addr
    forwarded = request.headers.get('X-Forwarded-For', '')
    if peer in TRUSTED_PROXIES and forwarded:
        # left-most address is the original client
        return forwarded.split(',')[0].strip()[:64] or peer
    return peer


def user_agent() -> str | None:
    return (request.headers.get('User-Agent') or '')[:400] or None if has_request_context() else None


def describe_device(ua: str | None) -> str:
    """'Chrome · Windows' style label from a User-Agent string."""
    if not ua:
        return '—'
    browser = next((name for pattern, name in (
        (r'Edg/', 'Edge'), (r'OPR/|Opera', 'Opera'), (r'Chrome/', 'Chrome'),
        (r'Firefox/', 'Firefox'), (r'Safari/', 'Safari'), (r'curl/|python-requests|Postman', 'Script/API'),
    ) if re.search(pattern, ua)), 'Browser')
    system = next((name for pattern, name in (
        (r'Windows', 'Windows'), (r'Android', 'Android'), (r'iPhone|iPad', 'iOS'),
        (r'Mac OS X', 'macOS'), (r'Linux', 'Linux'),
    ) if re.search(pattern, ua)), '')
    return f'{browser} · {system}' if system else browser


def is_public(ip: str | None) -> bool:
    try:
        addr = ipaddress.ip_address(ip or '')
        return not (addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local)
    except ValueError:
        return False


def geolocate(ip: str | None) -> dict:
    """
    Approximate location + network type of an IP (ip-api.com, cached in memory).
    Private addresses (local network, dev machine) are labelled as such.
    `proxy`/`hosting` flag VPNs, Tor exits and datacentre addresses.
    """
    if not ip:
        return {}
    if not is_public(ip):
        return {'local': True}
    if ip in _geo_cache:
        return _geo_cache[ip]
    try:
        data = requests.get(GEO_URL.format(ip=ip), timeout=3).json()
    except (requests.RequestException, ValueError) as exc:
        logger.info('IP geolocation unavailable for %s: %s', ip, exc)
        return {}
    if data.get('status') != 'success':
        return {}
    geo = {
        'country': data.get('country'), 'country_code': data.get('countryCode'),
        'region': data.get('regionName'), 'city': data.get('city'),
        'isp': data.get('isp') or data.get('org'), 'asn': data.get('as'),
        'proxy': bool(data.get('proxy')), 'hosting': bool(data.get('hosting')),
        'mobile': bool(data.get('mobile')),
    }
    _geo_cache[ip] = geo
    return geo
