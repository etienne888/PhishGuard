"""
URL feature extraction for phishing detection.

Pure-Python + numpy + tldextract. No scikit-learn dependency.

Every feature is:
- deterministic (same URL → same features)
- bounded (documented range)
- fast (< 1 ms per URL)

Feature groups:
1. Structural:  length, depth, subdomains, digits, entropy
2. Lexical:     hyphens, dots, @, %, punycode, hex escapes
3. Semantic:    suspicious TLD, brand lookalike distance, credential paths
4. Protocol:    HTTPS, port, IP-literal host
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Optional
from urllib.parse import urlparse

import numpy as np
import tldextract

# Use a bundled snapshot of the public suffix list to avoid network calls.
# tldextract will fall back to bundled data if `.live` is not called.
_extractor = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# High-abuse TLDs (source: Spamhaus / Interisle 2024)
SUSPICIOUS_TLDS = frozenset({
    "tk", "ml", "ga", "cf", "gq",           # Freenom
    "top", "xyz", "click", "link",          # High-abuse gTLDs
    "zip", "mov",                            # Deceptive TLDs
    "work", "loan", "review", "country",
    "kim", "date", "racing", "party",
})

# Brands frequently impersonated in Cameroon / West Africa
PROTECTED_BRANDS = (
    "mtn", "orange", "camtel", "nexttel",
    "afriland", "bicec", "sgbc", "uba", "ecobank", "cbc", "scb",
    "cnps", "crtv", "eneo", "camwater",
    "momo", "orangemoney", "mtnmomo",
    "whatsapp", "facebook", "google", "microsoft",
    "apple", "paypal", "netflix", "amazon", "dhl", "fedex",
)

# Path keywords commonly used in phishing landing pages
CREDENTIAL_PATH_KEYWORDS = frozenset({
    "login", "signin", "verify", "confirm", "account",
    "password", "secure", "update", "validate", "auth",
})

_IPV4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_HEX_ESCAPE_RE = re.compile(r"%[0-9A-Fa-f]{2}")

# Feature order is frozen — the trained model depends on it.
FEATURE_NAMES = [
    # 1. Structural
    "url_length",
    "host_length",
    "path_length",
    "subdomain_count",
    "dot_count",
    "hyphen_count",
    "digit_count",
    "digit_ratio",
    "host_entropy",
    "path_entropy",
    "query_param_count",
    "path_depth",
    "has_query",
    # 2. Lexical
    "has_at_symbol",
    "has_punycode",
    "has_hex_escape",
    "has_double_slash_in_path",
    "has_http_in_path",
    "has_port_explicit",
    "uppercase_ratio",
    # 3. Semantic
    "is_ip_literal",
    "has_suspicious_tld",
    "brand_distance_min",
    "brand_exact_match",
    "has_credential_path",
    "has_suspicious_keyword",
    # 4. Protocol
    "is_https",
    "has_www",
    "is_shortener",
    "subdomain_is_ip",
]

NUM_FEATURES = len(FEATURE_NAMES)

_SHORTENERS = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "is.gd", "buff.ly", "rebrand.ly", "cutt.ly", "shorturl.at",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _levenshtein(a: str, b: str, max_dist: int = 3) -> int:
    """Bounded Levenshtein. Returns max_dist+1 if exceeded."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) > max_dist:
        return max_dist + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            curr[j] = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + (ca != cb),
            )
        prev = curr
    return prev[-1]


def _min_brand_distance(label: str) -> int:
    """Smallest Levenshtein distance from a domain label to any brand."""
    if not label:
        return 99
    candidates = [part for part in re.split(r"[-_]", label) if part]
    candidates.append(label.replace("-", "").replace("_", ""))
    best = 99
    for candidate in candidates:
        for brand in PROTECTED_BRANDS:
            d = _levenshtein(candidate, brand, max_dist=3)
            if d < best:
                best = d
                if best == 0:
                    return best
    return best


def _safe_hostname(parsed) -> str:
    host = (parsed.hostname or "").lower()
    return host


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_url_features(url: str) -> np.ndarray:
    """
    Return a 1-D numpy array of NUM_FEATURES floats for the given URL.

    Never raises — malformed URLs degrade to all-zero features.
    """
    if not url or not isinstance(url, str):
        return np.zeros(NUM_FEATURES, dtype=np.float32)

    raw = url.strip()

    # Add a scheme if missing so urlparse doesn't put everything in `path`.
    if "://" not in raw:
        parse_target = "http://" + raw
    else:
        parse_target = raw

    try:
        parsed = urlparse(parse_target)
    except Exception:
        return np.zeros(NUM_FEATURES, dtype=np.float32)

    host = _safe_hostname(parsed)
    path = parsed.path or ""
    query = parsed.query or ""

    # tldextract for correct public-suffix handling (e.g. com.cm)
    ext = _extractor(host)
    subdomain = ext.subdomain or ""
    domain = ext.domain or ""
    suffix = ext.suffix or ""

    full_domain = ".".join(p for p in [domain, suffix] if p)
    label = domain  # main label, e.g. "mtn" in "mtn.cm"

    # ---------- 1. Structural ----------
    url_length = len(raw)
    host_length = len(host)
    path_length = len(path)
    subdomain_count = len([s for s in subdomain.split(".") if s]) if subdomain else 0
    dot_count = host.count(".")
    hyphen_count = host.count("-") + path.count("-")
    digit_count = sum(c.isdigit() for c in host) + sum(c.isdigit() for c in path)
    digit_ratio = digit_count / max(len(host) + len(path), 1)
    host_entropy = _shannon_entropy(host)
    path_entropy = _shannon_entropy(path)
    query_param_count = query.count("&") + 1 if query else 0
    path_depth = len([p for p in path.split("/") if p])
    has_query = 1.0 if query else 0.0

    # ---------- 2. Lexical ----------
    has_at_symbol = 1.0 if "@" in raw else 0.0
    has_punycode = 1.0 if "xn--" in host else 0.0
    has_hex_escape = 1.0 if _HEX_ESCAPE_RE.search(raw) else 0.0
    has_double_slash_in_path = 1.0 if "//" in path else 0.0
    has_http_in_path = 1.0 if "http" in path.lower() else 0.0
    has_port_explicit = 1.0 if parsed.port is not None else 0.0
    letters = [c for c in host if c.isalpha()]
    uppercase_ratio = (
        sum(c.isupper() for c in letters) / len(letters)
        if letters else 0.0
    )

    # ---------- 3. Semantic ----------
    is_ip_literal = 1.0 if _IPV4_RE.match(host) else 0.0
    has_suspicious_tld = 1.0 if suffix.lower() in SUSPICIOUS_TLDS else 0.0
    brand_distance = float(min(_min_brand_distance(label), 10))
    brand_exact = 1.0 if label.lower() in PROTECTED_BRANDS else 0.0
    path_lower = path.lower()
    has_credential_path = 1.0 if any(kw in path_lower for kw in CREDENTIAL_PATH_KEYWORDS) else 0.0
    has_suspicious_keyword = 1.0 if (
        "secure" in host or "verify" in host or "login" in host or "account" in host
    ) else 0.0

    # ---------- 4. Protocol ----------
    is_https = 1.0 if parsed.scheme.lower() == "https" else 0.0
    has_www = 1.0 if host.startswith("www.") else 0.0
    is_shortener = 1.0 if full_domain in _SHORTENERS else 0.0
    subdomain_is_ip = 1.0 if _IPV4_RE.match(subdomain or "") else 0.0

    return np.array([
        url_length, host_length, path_length, subdomain_count, dot_count,
        hyphen_count, digit_count, digit_ratio, host_entropy, path_entropy,
        query_param_count, path_depth, has_query,
        has_at_symbol, has_punycode, has_hex_escape,
        has_double_slash_in_path, has_http_in_path, has_port_explicit,
        uppercase_ratio,
        is_ip_literal, has_suspicious_tld, brand_distance, brand_exact,
        has_credential_path, has_suspicious_keyword,
        is_https, has_www, is_shortener, subdomain_is_ip,
    ], dtype=np.float32)


def extract_urls_from_text(text: str) -> list[str]:
    """Find all http/https URLs in a blob of text."""
    if not text:
        return []
    return re.findall(r"https?://[^\s<>\"']+", text, flags=re.IGNORECASE)