"""
Offline URL intelligence: structure checks + brand/whitelist checks.

Network checks (redirect following, blocklist feeds, WHOIS domain age) are
left as clearly marked extension points so the demo works without internet.
"""

import ipaddress
from urllib.parse import urlparse

from .sender import check_domain

SUSPICIOUS_TLDS = {".tk", ".ga", ".ml", ".cf", ".gq", ".xyz", ".top", ".icu", ".buzz", ".click"}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "ow.ly", "rb.gy", "shorturl.at"}
LURE_WORDS = ("login", "verify", "verif", "secure", "update", "account", "confirm", "reactiv", "bonus")


def analyze_url(url: str, whitelist: dict) -> dict:
    """Score one URL 0-100 and list the reasons, in French."""
    parsed = urlparse(url if "://" in url else f"http://{url}")
    host = (parsed.hostname or "").lower()
    score, reasons = 0, []

    domain_check = check_domain(host, whitelist)
    status = domain_check["status"]
    if status == "whitelisted":
        return {"url": url, "host": host, "score": 0, "reasons": [], "domain": domain_check,
                "blocklisted": False}
    if status == "lookalike":
        score += 60
        reasons.append(f"Domaine qui imite {domain_check['imitates']} ({domain_check['institution']})")
    elif status == "brand_impersonation":
        score += 50
        reasons.append(f"Le lien utilise le nom de {domain_check['institution']} sans être son site officiel")

    is_ip = False
    try:
        ipaddress.ip_address(host)
        is_ip = True
        score += 35
        reasons.append("Adresse IP utilisée à la place d'un nom de domaine")
    except ValueError:
        pass

    if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
        score += 30
        reasons.append(f"Extension de domaine très utilisée par les fraudeurs ({host.rsplit('.', 1)[-1]})")
    if host in SHORTENERS:
        score += 25
        reasons.append("Lien raccourci qui cache la vraie destination")
    if "xn--" in host:
        score += 30
        reasons.append("Domaine avec caractères déguisés (punycode)")
    if not is_ip and host.count(".") >= 3:
        score += 10
        reasons.append("Nombreux sous-domaines")
    if parsed.scheme == "http":
        score += 10
        reasons.append("Connexion non sécurisée (http)")
    if "@" in parsed.netloc:
        score += 25
        reasons.append("Identifiants cachés dans l'adresse du lien")
    if any(word in url.lower() for word in LURE_WORDS):
        score += 10
        reasons.append("Mots d'hameçonnage dans le lien (login, verify, secure…)")

    # EXTENSION POINTS (need network): follow redirects, OpenPhish/URLhaus
    # blocklist lookup (set "blocklisted": True), WHOIS domain age.
    return {"url": url, "host": host, "score": min(100, score), "reasons": reasons,
            "domain": domain_check, "blocklisted": False}


_xgb_model = None


def xgb_enabled() -> bool:
    # Off by default: the model trained by train_url.py (2026-09-24) learned
    # "URL has a path => phishing" because its legitimate URLs (Tranco) are bare
    # domains; it scores bbc.com/news/... and mtn.cm/particuliers/... at 100 %.
    # Set ENABLE_XGB_URL=true only after retraining on legitimate URLs with paths.
    import os
    return os.getenv('ENABLE_XGB_URL', 'false').lower() == 'true'


def get_xgb_model():
    """The trained XGBoost URL classifier (train_url.py), or None if unavailable."""
    global _xgb_model
    if _xgb_model is None:
        try:
            import os
            from app.ml_engine.url_model import URLClassifier
            path = os.path.join(os.path.dirname(__file__), '..', 'ml_engine', 'trained', 'url_model.pkl')
            _xgb_model = URLClassifier.load(path)
        except Exception:
            _xgb_model = False  # xgboost missing or model not trained
    return _xgb_model or None


def analyze_urls(urls: list[str], whitelist: dict) -> dict:
    results = [analyze_url(u, whitelist) for u in urls]
    model = get_xgb_model() if xgb_enabled() else None
    if model is not None:
        for r in results:
            if r['domain']['status'] == 'whitelisted':
                continue
            try:
                probability = float(model.predict_proba(r['url']))
            except Exception:
                continue
            r['xgb'] = round(probability * 100, 1)
            if probability >= 0.5:
                r['reasons'].append(f"Modèle XGB : lien malveillant à {probability * 100:.0f} %")
            # Rules catch local brand tricks, XGB catches generic URL patterns: keep the stronger
            r['score'] = max(r['score'], round(probability * 100))
    worst = max((r["score"] for r in results), default=0)
    return {"score": worst, "results": results,
            "blocklisted": any(r["blocklisted"] for r in results)}
