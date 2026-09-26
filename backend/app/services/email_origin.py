"""
Email origin tracing: where was this email really sent from?

Reads the "Received" chain (each mail server adds one line on top, so the
bottom line is the first hop), finds the first public sender IP, and enriches
it: approximate location (IP geolocation, with an honest accuracy radius),
network (ISP, AS, mobile / datacentre / proxy), reverse DNS, public DNS
blacklists, sending software, timezone - plus consistency checks such as
"claims to be MTN but sent from a datacentre abroad".

Honest limits, surfaced to users as `precision`:
  * IP geolocation is city-level at best (never a street address).
  * Webmail (Gmail, Outlook.com, Yahoo...) usually hides the sender's IP: we then
    report the provider, precision "hidden".
Only real emails (.eml, connected mailbox, forwarded email) carry this data.
"""
from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from email import policy
from email.parser import BytesHeaderParser
from email.utils import parsedate_to_datetime

import requests

log = logging.getLogger(__name__)

IP_API = ('http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,district,zip,'
          'lat,lon,timezone,offset,isp,org,as,asname,reverse,mobile,proxy,hosting,query')
IP_API_BATCH = 'http://ip-api.com/batch?fields=status,country,countryCode,city,lat,lon,isp,query'
DNSBLS = ('bl.spamcop.net', 'b.barracudacentral.org', 'dnsbl-1.uceprotect.net')
CACHE_TTL = 7 * 24 * 3600
_lock = threading.Lock()

# Mail providers whose servers appear in the chain (and usually hide the sender's IP)
PROVIDERS = [
    ('Gmail', ('google.com', 'gmail.com', 'googlemail.com')),
    ('Outlook / Microsoft 365', ('outlook.com', 'hotmail.com', 'protection.outlook.com', 'office365.com', 'microsoft.com')),
    ('Yahoo', ('yahoo.com', 'yahoodns.net')),
    ('Zoho', ('zoho.com', 'zohomail.com')),
    ('Proton', ('protonmail.ch', 'proton.me')),
    ('Amazon SES', ('amazonses.com',)),
    ('SendGrid', ('sendgrid.net',)),
    ('Mailchimp', ('mcsv.net', 'mcdlv.net', 'rsgsv.net')),
]

IP_RE = re.compile(r'\[(?:IPv6:)?([0-9a-fA-F:.]+)\]|\(([0-9]{1,3}(?:\.[0-9]{1,3}){3})\)')
FROM_RE = re.compile(r'^\s*from\s+(\S+)(.*?)(?=\sby\s|$)', re.IGNORECASE | re.DOTALL)
BY_RE = re.compile(r'\sby\s+(\S+)', re.IGNORECASE)
WITH_RE = re.compile(r'\swith\s+(\S+)', re.IGNORECASE)


# ------------------------------------------------------------------ helpers

def is_public(ip: str | None) -> bool:
    try:
        addr = ipaddress.ip_address(ip or '')
        return not (addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local
                    or addr.is_multicast or addr.is_unspecified)
    except ValueError:
        return False


def _provider(host: str | None) -> str | None:
    host = (host or '').lower().rstrip('.')
    for name, domains in PROVIDERS:
        if any(host == d or host.endswith('.' + d) for d in domains):
            return name
    return None


def _cache_file(instance_path: str | None) -> str | None:
    if not instance_path:
        return None
    os.makedirs(instance_path, exist_ok=True)
    return os.path.join(instance_path, 'ip_cache.json')


def _cache_get(path: str | None, ip: str) -> dict | None:
    if not path:
        return None
    try:
        with _lock, open(path, encoding='utf-8') as fh:
            row = json.load(fh).get(ip)
        return row if row and time.time() - row.get('ts', 0) < CACHE_TTL else None
    except (OSError, ValueError):
        return None


def _cache_put(path: str | None, ip: str, row: dict) -> None:
    if not path:
        return
    with _lock:
        try:
            with open(path, encoding='utf-8') as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            data = {}
        data[ip] = {**row, 'ts': time.time()}
        if len(data) > 5000:  # keep the file small
            data = dict(sorted(data.items(), key=lambda kv: kv[1].get('ts', 0))[-4000:])
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(data, fh)
        os.replace(tmp, path)


def geolocate_ip(ip: str, instance_path: str | None = None) -> dict | None:
    """Detailed IP intelligence (ip-api.com, free tier, HTTP, cached 7 days)."""
    cached = _cache_get(_cache_file(instance_path), ip)
    if cached:
        return {k: v for k, v in cached.items() if k != 'ts'}
    try:
        row = requests.get(IP_API.format(ip=ip), timeout=5).json()
    except (requests.RequestException, ValueError):
        return None
    if row.get('status') != 'success':
        return None
    geo = {
        'ip': ip, 'country': row.get('country'), 'country_code': row.get('countryCode'),
        'region': row.get('regionName'), 'city': row.get('city'), 'district': row.get('district') or None,
        'zip': row.get('zip') or None, 'lat': row.get('lat'), 'lon': row.get('lon'),
        'timezone': row.get('timezone'), 'utc_offset_s': row.get('offset'),
        'isp': row.get('isp'), 'org': row.get('org'), 'asn': (row.get('as') or '').split(' ')[0] or None,
        'as_name': row.get('asname'), 'reverse_dns': row.get('reverse') or None,
        'mobile': bool(row.get('mobile')), 'proxy': bool(row.get('proxy')), 'hosting': bool(row.get('hosting')),
    }
    _cache_put(_cache_file(instance_path), ip, geo)
    return geo


def _batch_locate(ips: list[str]) -> dict[str, dict]:
    if not ips:
        return {}
    try:
        rows = requests.post(IP_API_BATCH, json=ips[:20], timeout=5).json()
    except (requests.RequestException, ValueError):
        return {}
    return {r['query']: r for r in rows if r.get('status') == 'success'}


def _dnsbl(ip: str) -> list[str]:
    """Public DNS blacklists listing this IPv4 address."""
    try:
        if ipaddress.ip_address(ip).version != 4:
            return []
    except ValueError:
        return []
    reversed_ip = '.'.join(reversed(ip.split('.')))

    def listed(zone: str) -> str | None:
        try:
            answer = socket.gethostbyname(f'{reversed_ip}.{zone}')
            # 127.0.0.x = listed; anything else is a resolver error page or a refusal
            return zone if answer.startswith('127.0.0.') else None
        except (socket.gaierror, OSError, UnicodeError):
            return None

    old = socket.getdefaulttimeout()
    socket.setdefaulttimeout(2)
    try:
        with ThreadPoolExecutor(max_workers=len(DNSBLS)) as pool:
            return [z for z in pool.map(listed, DNSBLS) if z]
    finally:
        socket.setdefaulttimeout(old)


def _device(headers) -> dict:
    agent = headers.get('X-Mailer') or headers.get('User-Agent') or ''
    agent = str(agent)[:160]
    low = agent.lower()
    label = None
    for needle, name in (('iphone', 'iPhone Mail'), ('ipad', 'iPad Mail'), ('android', 'Android'),
                         ('outlook', 'Microsoft Outlook'), ('thunderbird', 'Thunderbird'), ('apple mail', 'Apple Mail'),
                         ('phpmailer', 'PHPMailer (web script)'), ('python', 'Python script'), ('swiftmailer', 'SwiftMailer (web script)'),
                         ('roundcube', 'Roundcube webmail'), ('sendgrid', 'SendGrid'), ('mailchimp', 'Mailchimp')):
        if needle in low:
            label = name
            break
    script = any(k in low for k in ('phpmailer', 'python', 'swiftmailer', 'perl', 'curl', 'nodemailer'))
    return {'agent': agent or None, 'label': label or (agent.split('/')[0][:40] if agent else None), 'scripted': script}


def _parse_hop(value: str) -> dict:
    value = ' '.join(str(value).split())
    head, _, date_part = value.rpartition(';')
    head = head or value
    hop: dict = {'raw': value[:400]}
    m = FROM_RE.match(head)
    if m:
        hop['from_host'] = m.group(1).strip('()[]')
        ip_m = IP_RE.search(m.group(2) or '') or IP_RE.search(m.group(1) or '')
        if ip_m:
            hop['from_ip'] = ip_m.group(1) or ip_m.group(2)
        rdns = re.search(r'\(([\w.-]+\.[a-z]{2,})\s*\[', m.group(2) or '')
        if rdns:
            hop['from_rdns'] = rdns.group(1)
    by = BY_RE.search(head)
    if by:
        hop['by_host'] = by.group(1).strip(';()')
    with_m = WITH_RE.search(head)
    if with_m:
        hop['protocol'] = with_m.group(1).strip(';')
    try:
        when = parsedate_to_datetime(date_part.strip()) if date_part else None
        hop['time'] = when.isoformat() if when else None
    except (TypeError, ValueError, IndexError):
        hop['time'] = None
    return hop


# ------------------------------------------------------------------ main

def trace(raw: bytes, *, claimed_brand: str | None = None, instance_path: str | None = None,
          network: bool = True) -> dict:
    """Full origin report for one raw email (admin view; see public_view for users)."""
    headers = BytesHeaderParser(policy=policy.default).parsebytes(raw)
    received = [str(v) for v in (headers.get_all('Received') or [])]
    hops = [_parse_hop(v) for v in reversed(received)]  # first hop first

    # Delay between consecutive hops
    from datetime import datetime
    previous = None
    for hop in hops:
        try:
            current = datetime.fromisoformat(hop['time']) if hop.get('time') else None
        except ValueError:
            current = None
        hop['delay_s'] = round((current - previous).total_seconds()) if current and previous else None
        previous = current or previous
        hop['provider'] = _provider(hop.get('by_host')) or _provider(hop.get('from_host'))

    providers = [h['provider'] for h in hops if h.get('provider')]
    provider = providers[0] if providers else None

    # The sender's IP: an explicit header when a webmail adds it, else the first public "from" IP
    explicit = None
    for name in ('X-Originating-IP', 'X-Sender-IP', 'X-Client-IP', 'X-Source-IP'):
        value = str(headers.get(name) or '').strip(' []')
        if is_public(value):
            explicit = (value, name)
            break
    sender_ip, how = (explicit[0], f'header {explicit[1]}') if explicit else (None, None)
    if not sender_ip:
        for hop in hops:
            if is_public(hop.get('from_ip')):
                sender_ip, how = hop['from_ip'], 'first public hop'
                hop['is_origin'] = True
                break

    report: dict = {
        'hops': hops, 'hop_count': len(hops), 'provider': provider, 'sender_ip': sender_ip, 'found_by': how,
        'device': _device(headers),
        'message_id_domain': (re.search(r'@([\w.-]+)>?\s*$', str(headers.get('Message-ID') or '')) or [None, None])[1],
        'date_header': str(headers.get('Date') or '') or None,
        'return_path': str(headers.get('Return-Path') or '').strip('<>') or None,
        'authentication': str(headers.get('Authentication-Results') or '')[:600] or None,
        'geo': None, 'blacklists': [], 'route': [], 'flags': [],
    }
    tz_match = re.search(r'([+-]\d{4})\s*(\(|$)', report['date_header'] or '')
    report['sender_utc_offset'] = tz_match.group(1) if tz_match else None

    # The origin is the provider's own server (webmail): the real sender is hidden
    origin_is_provider = sender_ip and any(h.get('is_origin') and h.get('provider') for h in hops)
    if not sender_ip or (origin_is_provider and not explicit):
        report['precision'] = 'hidden'
        report['flags'].append('hidden_by_provider' if provider else 'no_public_ip')

    hidden = report.get('precision') == 'hidden'
    if hidden and sender_ip:
        # The IP we found belongs to the provider (e.g. Google), not to the sender:
        # never place it on a map or judge it as if it were the sender's.
        report['provider_server'] = {'ip': sender_ip, 'host': next((h.get('from_host') for h in hops if h.get('is_origin')), None)}
        report['sender_ip'] = None
    if network and sender_ip and not hidden:
        with ThreadPoolExecutor(max_workers=3) as pool:
            geo_f = pool.submit(geolocate_ip, sender_ip, instance_path)
            bl_f = pool.submit(_dnsbl, sender_ip)
            relay_ips = list(dict.fromkeys(h['from_ip'] for h in hops if is_public(h.get('from_ip')) and h['from_ip'] != sender_ip))[:6]
            relays_f = pool.submit(_batch_locate, relay_ips)
            report['geo'], report['blacklists'], relays = geo_f.result(), bl_f.result(), relays_f.result()
        geo = report['geo']
        if geo:
            report['route'].append({'lat': geo['lat'], 'lon': geo['lon'], 'label': geo.get('city') or geo.get('country'),
                                    'kind': 'sender', 'ip': sender_ip})
        for ip in relay_ips:
            r = relays.get(ip)
            if r:
                report['route'].append({'lat': r['lat'], 'lon': r['lon'], 'label': r.get('city') or r.get('country'),
                                        'kind': 'relay', 'ip': ip, 'isp': r.get('isp')})

    geo = report['geo'] or {}
    if 'precision' not in report:
        if not geo:
            report['precision'] = 'low'
        elif geo.get('hosting') or geo.get('proxy'):
            report['precision'] = 'medium'  # we see the server, not the person behind it
        else:
            report['precision'] = 'high'
    # Honest accuracy radius of an IP location (km)
    report['accuracy_km'] = (None if not geo else 50 if geo.get('mobile') else 5 if geo.get('hosting') else 15)
    report['network_type'] = (None if not geo else 'proxy' if geo.get('proxy') else 'hosting' if geo.get('hosting')
                              else 'mobile' if geo.get('mobile') else 'fixed')

    # Consistency checks
    if geo.get('hosting'):
        report['flags'].append('datacenter')
    if geo.get('proxy'):
        report['flags'].append('proxy')
    if report['blacklists']:
        report['flags'].append('blacklisted')
    if report['device']['scripted']:
        report['flags'].append('scripted')
    if claimed_brand and geo.get('country_code') and geo['country_code'] != 'CM':
        report['flags'].append('foreign_for_local_brand')
    offset = report['sender_utc_offset']
    if offset and geo.get('utc_offset_s') is not None:
        sign = 1 if offset[0] == '+' else -1
        header_s = sign * (int(offset[1:3]) * 3600 + int(offset[3:5]) * 60)
        if abs(header_s - geo['utc_offset_s']) >= 3 * 3600:
            report['flags'].append('timezone_mismatch')
    if any((h.get('delay_s') or 0) > 3600 for h in hops):
        report['flags'].append('long_delay')
    report['claimed_brand'] = claimed_brand
    return report


def public_view(report: dict | None) -> dict | None:
    """What a regular user sees: approximate area, network, device family, warnings - no IPs, no headers."""
    if not report:
        return None
    geo = report.get('geo') or {}
    lat, lon = geo.get('lat'), geo.get('lon')
    return {
        'precision': report.get('precision'),
        'provider': report.get('provider'),
        'city': geo.get('city'), 'region': geo.get('region'), 'country': geo.get('country'),
        'country_code': geo.get('country_code'),
        # Rounded (~1 km): enough for an "approximate area" circle, not a pinpoint
        'lat': round(lat, 2) if lat is not None else None, 'lon': round(lon, 2) if lon is not None else None,
        'accuracy_km': report.get('accuracy_km'),
        'isp': geo.get('isp'), 'network_type': report.get('network_type'),
        'device': (report.get('device') or {}).get('label'),
        'flags': report.get('flags') or [],
        'hop_count': report.get('hop_count'),
    }
