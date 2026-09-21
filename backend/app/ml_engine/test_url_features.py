"""
Unit tests for URL feature extraction.

Run: pytest backend/tests/test_url_features.py -v
"""

import numpy as np
import pytest

from app.ml_engine.url_features import (
    FEATURE_NAMES,
    NUM_FEATURES,
    extract_url_features,
    extract_urls_from_text,
)


def _idx(name: str) -> int:
    return FEATURE_NAMES.index(name)


def _get(url: str, feature: str) -> float:
    vec = extract_url_features(url)
    return float(vec[_idx(feature)])


# ---------------------------------------------------------------------------
# Shape and safety
# ---------------------------------------------------------------------------

def test_feature_vector_length():
    vec = extract_url_features("https://example.com")
    assert vec.shape == (NUM_FEATURES,)
    assert vec.dtype == np.float32


def test_empty_url_returns_zeros():
    vec = extract_url_features("")
    assert np.all(vec == 0)


def test_none_safe():
    vec = extract_url_features(None)  # type: ignore[arg-type]
    assert np.all(vec == 0)


def test_malformed_url_does_not_raise():
    for bad in ["http://", "://", "ftp://x", "not a url at all", "//no-scheme"]:
        extract_url_features(bad)


# ---------------------------------------------------------------------------
# Structural features
# ---------------------------------------------------------------------------

def test_url_length():
    url = "https://example.com/path"
    assert _get(url, "url_length") == len(url)


def test_subdomain_count_zero():
    assert _get("https://example.com", "subdomain_count") == 0


def test_subdomain_count_two():
    assert _get("https://a.b.example.com", "subdomain_count") == 2


def test_path_depth():
    assert _get("https://example.com/a/b/c", "path_depth") == 3


def test_query_params():
    assert _get("https://example.com/?a=1&b=2", "query_param_count") == 2


# ---------------------------------------------------------------------------
# Lexical features
# ---------------------------------------------------------------------------

def test_has_at_symbol_true():
    assert _get("https://user@evil.com", "has_at_symbol") == 1.0


def test_has_at_symbol_false():
    assert _get("https://example.com", "has_at_symbol") == 0.0


def test_punycode_detected():
    assert _get("https://xn--80ak6aa92e.com", "has_punycode") == 1.0


def test_hex_escape_detected():
    assert _get("https://example.com/%2e%2e/admin", "has_hex_escape") == 1.0


def test_no_hex_escape():
    assert _get("https://example.com/path", "has_hex_escape") == 0.0


# ---------------------------------------------------------------------------
# Semantic features
# ---------------------------------------------------------------------------

def test_ip_literal_detected():
    assert _get("http://192.168.1.1/admin", "is_ip_literal") == 1.0


def test_ip_literal_false():
    assert _get("https://example.com", "is_ip_literal") == 0.0


def test_suspicious_tld_true():
    assert _get("http://mtn-secure.tk/verify", "has_suspicious_tld") == 1.0


def test_suspicious_tld_false():
    assert _get("https://orange.cm", "has_suspicious_tld") == 0.0


def test_brand_exact_match():
    assert _get("https://mtn.cm", "brand_exact_match") == 1.0


def test_brand_lookalike_distance_small():
    # "mtn" with a trailing "n" has distance 1 to brand "mtn"
    assert _get("https://mtnn-secure.com", "brand_distance_min") <= 2


def test_credential_path_detected():
    assert _get("https://example.com/account/verify", "has_credential_path") == 1.0


def test_credential_path_false():
    assert _get("https://example.com/blog/post", "has_credential_path") == 0.0


# ---------------------------------------------------------------------------
# Protocol features
# ---------------------------------------------------------------------------

def test_https_detected():
    assert _get("https://example.com", "is_https") == 1.0


def test_http_not_https():
    assert _get("http://example.com", "is_https") == 0.0


def test_www_prefix():
    assert _get("https://www.example.com", "has_www") == 1.0


def test_shortener_bitly():
    assert _get("https://bit.ly/abc123", "is_shortener") == 1.0


def test_not_shortener():
    assert _get("https://example.com/abc", "is_shortener") == 0.0


# ---------------------------------------------------------------------------
# URL extraction from text
# ---------------------------------------------------------------------------

def test_extract_urls_empty():
    assert extract_urls_from_text("") == []


def test_extract_urls_single():
    urls = extract_urls_from_text("Click http://mtn-secure.tk/verify now")
    assert urls == ["http://mtn-secure.tk/verify"]


def test_extract_urls_multiple():
    text = "Visit https://a.com and http://b.tk/path"
    urls = extract_urls_from_text(text)
    assert "https://a.com" in urls
    assert "http://b.tk/path" in urls


def test_extract_urls_none_when_absent():
    assert extract_urls_from_text("No links here.") == []