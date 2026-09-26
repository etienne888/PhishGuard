"""
Live health of the official (allowlisted) domains.

For each institution domain: does it resolve (DNS), does HTTPS answer, how many
days before its TLS certificate expires, and how fast it responds. An expired
certificate or a dead official domain is itself a phishing risk (users get used
to warnings, attackers can re-register lapsed domains).
"""
from __future__ import annotations

import socket
import ssl
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

TIMEOUT = 4


def _tls_days_left(host: str) -> tuple[int | None, str | None]:
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
        expires = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        issuer = dict(x[0] for x in cert.get('issuer', [])).get('organizationName')
        return (expires - datetime.utcnow()).days, issuer
    except ssl.SSLCertVerificationError:
        return -1, None  # invalid / self-signed / expired certificate
    except (OSError, ValueError, KeyError):
        return None, None


def check(domain: str) -> dict:
    result: dict = {'checked_at': datetime.utcnow().isoformat()}
    started = time.perf_counter()
    try:
        result['ip'] = socket.gethostbyname(domain)
        result['dns'] = True
    except (socket.gaierror, UnicodeError, OSError):
        # many sites only answer on www.
        try:
            result['ip'] = socket.gethostbyname(f'www.{domain}')
            result['dns'] = True
            domain = f'www.{domain}'
        except (socket.gaierror, UnicodeError, OSError):
            return {**result, 'dns': False, 'https': False, 'status': 'offline'}
    days, issuer = _tls_days_left(domain)
    if (days is None or days < 0) and not domain.startswith('www.'):
        # Many institutions only serve HTTPS on www.
        www_days, www_issuer = _tls_days_left(f'www.{domain}')
        if www_days is not None and www_days >= 0:
            days, issuer = www_days, www_issuer
            result['https_host'] = f'www.{domain}'
    result['latency_ms'] = round((time.perf_counter() - started) * 1000)
    result['https'] = days is not None and days >= 0
    result['ssl_days_left'] = days
    result['ssl_issuer'] = issuer
    if days is None:
        result['status'] = 'no_https'
    elif days < 0:
        result['status'] = 'invalid_certificate'
    elif days < 21:
        result['status'] = 'expiring'
    else:
        result['status'] = 'online'
    return result


def check_many(domains: list[str]) -> dict[str, dict]:
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(domains, pool.map(check, domains)))
