"""
Fusion engine: combine the four independent signals into one explained score.

    A. ML model (TF-IDF / Naive Bayes)  30 %
    B. Claude semantic analysis         25 %
    C. URL intelligence                 25 %
    D. Rules + headers + whitelist      20 %

Unavailable signals (AI down, no URLs) have their weight redistributed
proportionally. Override rules then enforce hard evidence both ways.
"""

BASE_WEIGHTS = {"ml": 0.30, "ai": 0.25, "url": 0.25, "rules": 0.20}


def verdict_for(score: float) -> str:
    if score > 80:
        return "Critical"
    if score > 60:
        return "High"
    if score > 40:
        return "Medium"
    return "Low"


def fuse(signals: dict, facts: dict) -> dict:
    """
    signals: {"ml": float|None, "ai": float|None, "url": float|None, "rules": float|None}
    facts:   {"blocklisted", "brand_spoof", "sender_whitelisted", "auth_pass",
            "worst_url_score"}
    """
    available = {k: v for k, v in signals.items() if v is not None}
    total_weight = sum(BASE_WEIGHTS[k] for k in available) or 1.0
    weights = {k: round(BASE_WEIGHTS[k] / total_weight, 3) for k in available}
    score = sum(available[k] * weights[k] for k in available)

    overrides = []
    if facts.get("blocklisted") or facts.get("brand_spoof"):
        if score < 85:
            score = 85
            overrides.append("Preuve forte (usurpation de marque ou lien sur liste noire) : score minimum 85")
    elif facts.get("sender_whitelisted") and facts.get("auth_pass") and facts.get("worst_url_score", 0) < 30:
        if score > 30:
            score = 30
            overrides.append("Expéditeur officiel authentifié (SPF/DKIM/DMARC) sans lien suspect : score maximum 30")

    score = round(max(0.0, min(100.0, score)), 2)
    return {
        "score": score,
        "verdict": verdict_for(score),
        "weights": weights,
        "signals": {k: (round(v, 2) if v is not None else None) for k, v in signals.items()},
        "overrides": overrides,
    }
