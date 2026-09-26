"""
Sender and brand checks against the Cameroonian institutions whitelist.

Detects three things:
  - the sender domain is a known, legitimate institution (whitelisted)
  - a domain *looks like* a whitelisted one (typosquatting: mtnmobil3money.com)
  - a domain *names* a brand without belonging to it (mtn-secure-cm.tk)
"""

from difflib import SequenceMatcher

# Used when the database is unreachable; mirrors database/scripts/02_seed.sql
DEFAULT_WHITELIST = {
    "mtn.cm": "MTN Cameroon",
    "orange.cm": "Orange Cameroon",
    "camtel.cm": "CAMTEL",
    "afrilandfirstbank.com": "Afriland First Bank",
    "ubacameroon.com": "UBA Cameroon",
    "sgc.cm": "Société Générale Cameroun",
    "ecobank.cm": "Ecobank Cameroun",
    "biccm.cm": "BICEC",
    "antic.cm": "ANTIC",
    "cirt.cm": "CIRT-CM",
    "cnps.cm": "CNPS",
    "minpostel.gov.cm": "MINPOSTEL",
}

# Brand keywords that phishers put in fake domains, mapped to the institution
BRAND_KEYWORDS = {
    "mtn": "MTN Cameroon", "momo": "MTN Cameroon", "orange": "Orange Cameroon",
    "camtel": "CAMTEL", "afriland": "Afriland First Bank", "uba": "UBA Cameroon",
    "ecobank": "Ecobank Cameroun", "bicec": "BICEC", "cnps": "CNPS",
    "antic": "ANTIC", "impots": "Impôts Cameroun",
}

# Undo common digit-for-letter tricks (mtnmobil3money -> mtnmobilemoney)
_LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t"})


def load_whitelist() -> dict:
    """Read active whitelist domains from the DB, falling back to defaults."""
    try:
        from app.models import WhitelistDomain
        rows = WhitelistDomain.query.filter_by(is_active=True).all()
        if rows:
            return {row.domain.lower(): row.institution for row in rows}
    except Exception:
        pass
    return DEFAULT_WHITELIST


def load_blocklist() -> set:
    """Active blocked domains (incident response / threat intel), empty if the DB is unreachable."""
    try:
        from app.models import BlockedDomain
        return {row.domain.lower() for row in BlockedDomain.query.filter_by(is_active=True).all()}
    except Exception:
        return set()


def registered_domain(host: str) -> str:
    """Best-effort 'example.cm' from 'a.b.example.cm' (handles gov.cm, co.uk)."""
    parts = host.lower().strip(".").split(".")
    if len(parts) >= 3 and parts[-2] in {"gov", "co", "com", "org", "ac"}:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def check_domain(host: str | None, whitelist: dict) -> dict:
    """Classify one domain. Returns a dict with status + human explanation."""
    if not host:
        return {"status": "unknown"}
    host = host.lower()
    root = registered_domain(host)

    if root in whitelist:
        return {"status": "whitelisted", "institution": whitelist[root], "domain": host}

    label = root.split(".")[0]
    normalized = label.translate(_LEET)
    for legit, institution in whitelist.items():
        legit_label = legit.split(".")[0]
        ratio = SequenceMatcher(None, normalized, legit_label).ratio()
        if normalized != legit_label and ratio >= 0.8:
            return {"status": "lookalike", "institution": institution, "domain": host,
                    "imitates": legit}

    # A brand word anywhere in the full host (subdomains included)
    host_norm = host.translate(_LEET)
    for keyword, institution in BRAND_KEYWORDS.items():
        if keyword in host_norm.replace("-", ".").split(".") or keyword in normalized:
            return {"status": "brand_impersonation", "institution": institution, "domain": host}

    return {"status": "unlisted", "domain": host}
