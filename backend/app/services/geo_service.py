"""
Geolocate the servers hosting malicious links: domain -> IP (DNS) -> location (ip-api.com).

Results are cached in instance/geo_cache.json (7 days; failures 1 day) so each
domain is looked up at most once a week. ip-api's free tier is HTTP-only,
45 batch requests/min, non-commercial - fine for an academic prototype.
Locations are IP-based: city-level and approximate, never exact.
"""
from __future__ import annotations

import ipaddress
import json
import logging
import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import current_app

logger = logging.getLogger(__name__)

TTL_OK = 7 * 24 * 3600
TTL_FAIL = 24 * 3600
BATCH_URL = 'http://ip-api.com/batch?fields=status,message,country,countryCode,city,lat,lon,isp,org,as,query'
_lock = threading.Lock()


def _cache_path() -> str:
    os.makedirs(current_app.instance_path, exist_ok=True)
    return os.path.join(current_app.instance_path, 'geo_cache.json')


def _load_cache() -> dict:
    try:
        with open(_cache_path(), encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    tmp = _cache_path() + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(cache, fh)
    os.replace(tmp, _cache_path())


def _resolve(host: str) -> str | None:
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None, socket.AF_INET)
        return infos[0][4][0] if infos else None
    except (socket.gaierror, UnicodeError, OSError):
        return None


def _is_public(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return not (addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local)
    except ValueError:
        return False


def locate_hosts(hosts: list[str], retry_failed: bool = False) -> dict[str, dict]:
    """
    Return {host: {ip, lat, lon, city, country, country_code, isp, asn}} for the hosts that could be placed.
    retry_failed: ignore cached failures (domains that did not resolve last time).
    """
    now = time.time()
    with _lock:
        cache = _load_cache()
    fresh = {h: v for h, v in cache.items()
             if h in hosts and (v.get('ok') or not retry_failed)
             and now - v.get('ts', 0) < (TTL_OK if v.get('ok') else TTL_FAIL)}
    todo = [h for h in hosts if h not in fresh]

    if todo:
        with ThreadPoolExecutor(max_workers=8) as pool:
            ips = dict(zip(todo, pool.map(_resolve, todo)))
        lookups = {h: ip for h, ip in ips.items() if ip and _is_public(ip)}
        for h in todo:
            if h not in lookups:
                fresh[h] = {'ok': False, 'ts': now, 'reason': 'unresolved' if not ips.get(h) else 'private'}

        unique_ips = list(dict.fromkeys(lookups.values()))[:100]
        geo_by_ip = {}
        if unique_ips:
            try:
                response = requests.post(BATCH_URL, json=unique_ips, timeout=6)
                response.raise_for_status()
                geo_by_ip = {row.get('query'): row for row in response.json()}
            except (requests.RequestException, ValueError) as exc:
                logger.warning('Geolocation lookup failed: %s', exc)
        for h, ip in lookups.items():
            row = geo_by_ip.get(ip)
            if row and row.get('status') == 'success':
                fresh[h] = {
                    'ok': True, 'ts': now, 'ip': ip, 'lat': row['lat'], 'lon': row['lon'],
                    'city': row.get('city') or '', 'country': row.get('country') or '',
                    'country_code': row.get('countryCode') or '', 'isp': row.get('isp') or row.get('org') or '',
                    'asn': (row.get('as') or '').split(' ')[0],
                }
            elif ip not in geo_by_ip and unique_ips:
                continue  # service unreachable: don't cache, retry next time
            else:
                fresh[h] = {'ok': False, 'ts': now, 'ip': ip, 'reason': 'not_found'}

        with _lock:
            cache = _load_cache()
            cache.update({h: v for h, v in fresh.items() if h in todo})
            _save_cache(cache)

    return {h: v for h, v in fresh.items() if v.get('ok')}
