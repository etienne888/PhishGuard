# backend/app/ml_engine/preprocessing/text_processor.py
"""
Feature extraction for phishing detection.

Replaces the previous 6-feature extractor with a 40+ feature extractor
covering URL structure, sender domain signals, header authenticity,
content patterns, and lexical statistics.

Design constraints:
- No network calls by default (WHOIS/DNS are opt-in, cached, timeout-bounded).
- Deterministic: same input always produces the same output.
- Fast: total extraction cost < 5 ms per item on typical hardware.
- Backward compatible: `clean_text` and `extract_features` keep their names.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Optional
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Top 20 TLDs by abuse volume (source: Spamhaus / Interisle 2024).
# Used both as a categorical feature and as a reputation signal.
SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq",          # Freenom family — classic abuse
    "top", "xyz", "click", "link",          # High-abuse gTLDs
    "zip", "mov",                            # Deceptive TLDs
    "work", "loan", "review", "country",    # Spam-heavy
    "kim", "date", "racing", "party",       # Low-reputation
}

# Brands frequently impersonated in Cameroon / West Africa context.
# Extend this list as you collect real data.
PROTECTED_BRANDS = [
    "mtn", "orange", "camtel", "nexttel",
    "afriland", "bicec", "sgbc", "uba", "ecobank", "cbc", "scb",
    "cnps", "crtv", "enéo", "eneo", "camwater",
    "momo", "orangemoney", "mtnmomo",
    "whatsapp", "facebook", "google", "microsoft", "apple", "paypal",
    "netflix", "amazon", "dhl", "fedex",
]

# Words that correlate strongly with phishing in our labeled corpus.
URGENCY_WORDS = {
    "urgent", "immediat", "immediate", "immediatement",
    "bloque", "bloquee", "suspends", "suspendu", "suspendue",
    "verifier", "verifiez", "verify", "confirmer", "confirmez",
    "cliquez", "cliquer", "click", "clique",
    "24h", "48h", "aujourd", "maintenant", "now",
    "expire", "expiration", "expirera",
    "dernier", "derniere", "final", "last",
    "action", "requise", "required", "immediate",
    "alerte", "alert", "attention", "warning",
}

CREDENTIAL_WORDS = {
    "mot", "passe", "password", "passwd",
    "identifiant", "identifiants", "login", "username",
    "code", "pin", "otp", "token", "authentification", "auth",
    "compte", "account", "profil", "profile",
    "confidentiel", "confidential", "secret",
    "numero", "carte", "card", "cvv", "expiration",
}

MONEY_WORDS = {
    "argent", "money", "frais", "fcfa", "cfa", "euro", "dollar",
    "transfert", "transfer", "paiement", "payment",
    "remboursement", "refund", "gain", "gagner", "prime", "reward",
    "facture", "invoice", "solde", "balance",
}

# Character classes for entropy / obfuscation detection.
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_EMAIL_RE = re.compile(r"[\w\.\-+]+@[\w\.\-]+")
_HEX_ESCAPE_RE = re.compile(r"%[0-9A-Fa-f]{2}")


# ---------------------------------------------------------------------------
# Small helpers (all pure, all cheap)
# ---------------------------------------------------------------------------

def _shannon_entropy(s: str) -> float:
    """Shannon entropy of a string, in bits. Returns 0.0 for empty strings."""
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def _levenshtein(a: str, b: str, max_dist: int = 3) -> int:
    """
    Bounded Levenshtein distance. Returns max_dist+1 if the true distance
    exceeds max_dist, which is fine because we only care about near-matches.
    """
    if a == b:
        return 0
    if abs(len(a) - len(b)) > max_dist:
        return max_dist + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            current[j] = min(
                previous[j] + 1,           # deletion
                current[j - 1] + 1,        # insertion
                previous[j - 1] + (ca != cb),  # substitution
            )
        previous = current
    return previous[-1]


def _extract_domain_from_sender(sender: Optional[str]) -> str:
    """Best-effort extraction of a domain from a sender string."""
    if not sender:
        return ""
    sender = sender.strip().lower()
    if "@" in sender:
        return sender.rsplit("@", 1)[-1]
    return sender


def _safe_urlparse(url: str):
    """urlparse that never raises."""
    try:
        return urlparse(url)
    except Exception:
        return urlparse("")


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class TextProcessor:
    """
    Extracts features from raw message text.

    Public API (unchanged from previous version):
        - clean_text(text) -> str
        - extract_features(text, sender_domain=None) -> dict[str, float|int]
    """

    # ------------------------------------------------------------------ clean
    def clean_text(self, text: str) -> str:
        """Lowercase, strip accents, remove URLs and non-alphanumerics."""
        if not text:
            return ""
        text = text.lower()
        text = "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        text = _URL_RE.sub(" urlplaceholder ", text)
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return text.strip()

    # --------------------------------------------------------------- features
    def extract_features(
        self,
        text: str,
        sender_domain: Optional[str] = None,
    ) -> dict[str, float]:
        """
        Return a flat dict of named numeric features.

        All values are floats (or ints castable to float) so they can be fed
        directly into any scikit-learn / XGBoost estimator.

        Feature groups:
          1. Lexical  — length, word stats, entropy, punctuation
          2. Urgency  — counts of urgency / credential / money keywords
          3. URL      — structure of every URL found in the text
          4. Sender   — domain shape, brand similarity, TLD reputation
          5. Auth     — SPF / DKIM / DMARC flags (when provided by caller)
        """
        raw_text = text or ""
        cleaned = self.clean_text(raw_text)
        words = cleaned.split()
        word_count = len(words)
        unique_words = len(set(words))

        # ---------- 1. Lexical ----------
        features: dict[str, float] = {
            "char_count": float(len(raw_text)),
            "word_count": float(word_count),
            "unique_word_count": float(unique_words),
            "avg_word_length": float(
                sum(len(w) for w in words) / word_count if word_count else 0.0
            ),
            "char_entropy": _shannon_entropy(raw_text),
            "digit_ratio": self._ratio(raw_text, str.isdigit),
            "upper_ratio": self._ratio(raw_text, str.isupper),
            "punct_ratio": self._ratio(raw_text, lambda c: not c.isalnum() and not c.isspace()),
            "exclamation_count": float(raw_text.count("!")),
            "question_count": float(raw_text.count("?")),
            "all_caps_word_count": float(
                sum(1 for w in raw_text.split() if len(w) > 2 and w.isupper())
            ),
        }

        # ---------- 2. Keyword categories ----------
        features["urgency_word_count"] = float(self._count_keywords(cleaned, URGENCY_WORDS))
        features["credential_word_count"] = float(self._count_keywords(cleaned, CREDENTIAL_WORDS))
        features["money_word_count"] = float(self._count_keywords(cleaned, MONEY_WORDS))
        features["urgency_density"] = features["urgency_word_count"] / max(word_count, 1)
        features["credential_density"] = features["credential_word_count"] / max(word_count, 1)
        features["money_density"] = features["money_word_count"] / max(word_count, 1)

        # ---------- 3. URL features ----------
        urls = _URL_RE.findall(raw_text)
        features["url_count"] = float(len(urls))
        features["has_url"] = 1.0 if urls else 0.0

        if urls:
            url_stats = [self._url_stats(u) for u in urls]
            features["url_avg_length"] = sum(s["length"] for s in url_stats) / len(url_stats)
            features["url_max_length"] = max(s["length"] for s in url_stats)
            features["url_has_ip"] = float(any(s["has_ip"] for s in url_stats))
            features["url_has_https"] = float(any(s["has_https"] for s in url_stats))
            features["url_avg_subdomains"] = sum(s["subdomain_count"] for s in url_stats) / len(url_stats)
            features["url_max_path_depth"] = max(s["path_depth"] for s in url_stats)
            features["url_has_at_symbol"] = float(any(s["has_at"] for s in url_stats))
            features["url_has_punycode"] = float(any(s["has_punycode"] for s in url_stats))
            features["url_has_hex_escape"] = float(any(s["has_hex_escape"] for s in url_stats))
            features["url_has_suspicious_tld"] = float(any(s["has_suspicious_tld"] for s in url_stats))
            features["url_has_credential_path"] = float(any(s["has_credential_path"] for s in url_stats))
        else:
            for key in (
                "url_avg_length", "url_max_length", "url_has_ip", "url_has_https",
                "url_avg_subdomains", "url_max_path_depth", "url_has_at_symbol",
                "url_has_punycode", "url_has_hex_escape", "url_has_suspicious_tld",
                "url_has_credential_path",
            ):
                features[key] = 0.0

        # ---------- 4. Sender domain features ----------
        domain = _extract_domain_from_sender(sender_domain)
        if domain:
            features["sender_domain_length"] = float(len(domain))
            features["sender_domain_entropy"] = _shannon_entropy(domain)
            features["sender_domain_dot_count"] = float(domain.count("."))
            features["sender_domain_dash_count"] = float(domain.count("-"))
            features["sender_domain_digit_ratio"] = self._ratio(domain, str.isdigit)
            features["sender_domain_has_suspicious_tld"] = float(
                self._tld_of(domain) in SUSPICIOUS_TLDS
            )
            features["sender_domain_brand_distance"] = float(
                self._min_brand_distance(domain)
            )
            features["sender_domain_is_brand_exact"] = float(
                self._is_brand_exact(domain)
            )
        else:
            for key in (
                "sender_domain_length", "sender_domain_entropy",
                "sender_domain_dot_count", "sender_domain_dash_count",
                "sender_domain_digit_ratio", "sender_domain_has_suspicious_tld",
                "sender_domain_brand_distance", "sender_domain_is_brand_exact",
            ):
                features[key] = 0.0

        # ---------- 5. Auth flags (optional — caller must provide) ----------
        # These default to 0 (unknown) and are meant to be overridden
        # by the API layer when the caller has real email headers.
        features.setdefault("spf_pass", 0.0)
        features.setdefault("dkim_pass", 0.0)
        features.setdefault("dmarc_pass", 0.0)
        features.setdefault("reply_to_mismatch", 0.0)

        # ---------- 6. Derived: brand-vs-domain mismatch ----------
        # If the text mentions a protected brand but the sender domain
        # is neither that brand nor a sanctioned variant, that's a strong signal.
        text_brands = {b for b in PROTECTED_BRANDS if b in cleaned}
        domain_brands = {b for b in PROTECTED_BRANDS if b in domain}
        features["brand_mentioned_in_text"] = float(len(text_brands) > 0)
        features["brand_in_sender_domain"] = float(len(domain_brands) > 0)
        features["brand_mismatch"] = float(
            len(text_brands) > 0 and len(domain_brands) == 0
        )

        return features

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _ratio(s: str, predicate) -> float:
        if not s:
            return 0.0
        return sum(1 for c in s if predicate(c)) / len(s)

    @staticmethod
    def _count_keywords(text: str, keywords: set[str]) -> int:
        """Count keyword occurrences using word boundaries (best-effort)."""
        # `text` is already cleaned (lowercased, unaccented, punctuation removed).
        tokens = text.split()
        token_set = set(tokens)
        # Single-word exact matches
        exact = sum(1 for kw in keywords if kw in token_set)
        # Multi-word phrases (e.g. "mot de passe") matched as substrings
        phrases = sum(1 for kw in keywords if " " in kw and kw in text)
        return exact + phrases

    @staticmethod
    def _tld_of(domain: str) -> str:
        parts = domain.split(".")
        return parts[-1] if parts else ""

    @staticmethod
    def _min_brand_distance(domain: str) -> int:
        """Smallest Levenshtein distance between the domain's main label
        and any protected brand. Lower = more suspicious."""
        if not domain:
            return 99
        label = domain.split(".")[0]  # strip TLD and subdomains
        label = label.replace("-", "")
        best = 99
        for brand in PROTECTED_BRANDS:
            d = _levenshtein(label, brand, max_dist=3)
            if d < best:
                best = d
                if best == 0:
                    break
        return best

    @staticmethod
    def _is_brand_exact(domain: str) -> bool:
        if not domain:
            return False
        label = domain.split(".")[0]
        return label in PROTECTED_BRANDS

    @staticmethod
    def _url_stats(url: str) -> dict:
        """Compute cheap structural features for one URL."""
        parsed = _safe_urlparse(url)
        host = (parsed.hostname or "").lower()
        path = (parsed.path or "").lower()

        subdomain_count = max(host.count(".") - 1, 0) if host else 0
        path_depth = len([p for p in path.split("/") if p])

        return {
            "length": len(url),
            "has_https": url.lower().startswith("https://"),
            "has_ip": bool(_IPV4_RE.search(host)),
            "subdomain_count": subdomain_count,
            "path_depth": path_depth,
            "has_at": "@" in url,
            "has_punycode": "xn--" in host,
            "has_hex_escape": bool(_HEX_ESCAPE_RE.search(url)),
            "has_suspicious_tld": host.split(".")[-1] in SUSPICIOUS_TLDS if host else False,
            "has_credential_path": any(
                kw in path for kw in ("login", "verify", "confirm", "account", "password", "signin")
            ),
        }