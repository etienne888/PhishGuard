"""
PhishGuard-AI v2 analysis pipeline.

    parse -> [ML | Claude AI | URL intel | rules+headers] in parallel -> fusion

Entry point: run_pipeline(text=... | raw_eml=..., source="web").
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor

from .ai_analyzer import MODEL as AI_MODEL, ai_risk_score, analyze_with_ai
from .fusion import fuse
from .parser import ParseError, ParsedMessage, parse_eml, parse_text
from .sender import check_domain, load_whitelist
from .url_intel import analyze_urls

__all__ = ["run_pipeline", "ParseError"]

MIN_TEXT_LENGTH = 10
_ml_model = None


def _load_ml_model():
    global _ml_model
    if _ml_model is None:
        from app.ml_engine.model_manager import NaiveBayesClassifier
        path = os.path.join(os.path.dirname(__file__), "..", "ml_engine", "trained", "classifier.joblib")
        try:
            _ml_model = NaiveBayesClassifier().load(path)
        except Exception:
            _ml_model = False  # remember the failure; don't retry every request
    return _ml_model or None


def _ml_signal(text: str):
    model = _load_ml_model()
    if model is None:
        return None
    try:
        return model.predict_proba(text) * 100
    except Exception:
        return None


def _rules_signal(msg: ParsedMessage, whitelist: dict):
    """Keyword heuristics + sender/header evidence. Returns (score, evidence, facts)."""
    from app.ml_engine.heuristic_scorer import HeuristicScorer

    score = HeuristicScorer().score(msg.text, msg.sender_domain)
    evidence, facts = [], {}
    lower = msg.text.lower()

    for word, label in (("urgent", "urgence"), ("bloqu", "menace de blocage"),
                        ("suspendu", "menace de suspension"), ("24h", "délai artificiel")):
        if word in lower:
            evidence.append(f"Pression psychologique : {label}")
    for word in ("code pin", "mot de passe", "otp", "code secret", "identifiant"):
        if word in lower:
            evidence.append(f"Demande d'information confidentielle : « {word} »")
            score += 10

    sender_check = check_domain(msg.sender_domain, whitelist)
    if sender_check["status"] == "whitelisted":
        facts["sender_whitelisted"] = True
        evidence.append(f"Expéditeur officiel : {sender_check['institution']} ({msg.sender_domain})")
    elif sender_check["status"] in ("lookalike", "brand_impersonation"):
        facts["brand_spoof"] = True
        score += 40
        evidence.append(f"L'expéditeur imite {sender_check['institution']} : {msg.sender_domain}")

    if msg.reply_to_domain and msg.sender_domain and msg.reply_to_domain != msg.sender_domain:
        score += 15
        evidence.append(f"Les réponses partent vers un autre domaine ({msg.reply_to_domain})")

    auth = msg.auth_results
    failed = [m.upper() for m, r in auth.items() if r in ("fail", "softfail", "none")]
    if failed:
        score += 20
        evidence.append(f"Échec de l'authentification de l'expéditeur : {', '.join(failed)}")
    facts["auth_pass"] = bool(auth) and all(r == "pass" for r in auth.values())

    risky_ext = (".exe", ".scr", ".js", ".vbs", ".apk", ".bat", ".iso", ".docm", ".xlsm", ".html")
    for att in msg.attachments:
        if att["filename"].lower().endswith(risky_ext):
            score += 30
            evidence.append(f"Pièce jointe dangereuse : {att['filename']}")

    return min(100, score), evidence, facts


def run_pipeline(text: str | None = None, raw_eml: bytes | None = None, source: str = "web") -> dict:
    started = time.perf_counter()
    msg = parse_eml(raw_eml) if raw_eml is not None else parse_text(text or "")
    if len(msg.text) < MIN_TEXT_LENGTH:
        raise ParseError("Message trop court pour être analysé (10 caractères minimum).")

    whitelist = load_whitelist()  # needs app context -> read before threads

    # The AI call is the slow part (network); run everything in parallel
    with ThreadPoolExecutor(max_workers=3) as pool:
        ai_future = pool.submit(analyze_with_ai, msg.text)
        ml_future = pool.submit(_ml_signal, msg.text)
        url_future = pool.submit(analyze_urls, msg.urls, whitelist)
        rules_score, rules_evidence, facts = _rules_signal(msg, whitelist)
        ai_verdict, ml_score, url_intel = ai_future.result(), ml_future.result(), url_future.result()

    brand_spoof_url = any(r["domain"]["status"] in ("lookalike", "brand_impersonation")
                        for r in url_intel["results"])
    facts.update({
        "blocklisted": url_intel["blocklisted"],
        "brand_spoof": facts.get("brand_spoof") or brand_spoof_url,
        "worst_url_score": url_intel["score"],
    })

    fused = fuse({
        "ml": ml_score,
        "ai": ai_risk_score(ai_verdict) if ai_verdict else None,
        "url": url_intel["score"] if msg.urls else None,
        "rules": rules_score,
    }, facts)

    evidence = list(rules_evidence)
    for r in url_intel["results"]:
        evidence.extend(f"{reason} — {r['host']}" for reason in r["reasons"])
    if ai_verdict:
        evidence.extend(f"IA : {reason}" for reason in ai_verdict.reasons)

    return {
        **fused,
        "evidence": evidence,
        "ai": ai_verdict.model_dump() if ai_verdict else None,
        "ai_model": AI_MODEL if ai_verdict else None,
        "urls": url_intel["results"],
        "message": {
            "source": source,
            "type": msg.source_type,
            "subject": msg.subject,
            "sender": msg.sender,
            "sender_domain": msg.sender_domain,
            "auth_results": msg.auth_results,
            "attachments": msg.attachments,
        },
        "recommendation": (ai_verdict.recommendation if ai_verdict else
                        "Ne cliquez sur aucun lien et vérifiez auprès du canal officiel. "
                        "Signalez au CIRT-CM : 8202 / alerts@cirt.cm"),
        "duration_ms": round((time.perf_counter() - started) * 1000),
    }