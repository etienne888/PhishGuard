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
from .i18n import DEFAULT_LANG, normalize_lang, tr
from .parser import ParseError, ParsedMessage, parse_eml, parse_text
from .sender import check_domain, load_blocklist, load_whitelist
from .url_intel import analyze_urls

__all__ = ["run_pipeline", "ParseError", "normalize_lang"]

MIN_TEXT_LENGTH = 10
# Origin findings worth showing as evidence (the others are only shown in the origin panel)
ORIGIN_EVIDENCE = ("foreign_for_local_brand", "datacenter", "proxy", "blacklisted", "scripted", "timezone_mismatch")


def _trace_origin(raw_eml: bytes, instance_path: str | None):
    """Origin report; never breaks the analysis (network errors -> partial report or None)."""
    try:
        from app.services.email_origin import trace
        return trace(raw_eml, instance_path=instance_path)
    except Exception:
        return None
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


def _rules_signal(msg: ParsedMessage, whitelist: dict, lang: str = DEFAULT_LANG):
    """Keyword heuristics + sender/header evidence.

    Returns (score, evidence, positives, facts); positives[i] is True when
    evidence[i] is reassuring (an official sender).
    """
    from app.ml_engine.heuristic_scorer import HeuristicScorer

    score = HeuristicScorer().score(msg.text, msg.sender_domain)
    evidence, positives, facts = [], [], {}
    lower = msg.text.lower()

    def add(text: str, positive: bool = False):
        evidence.append(text)
        positives.append(positive)

    # French and English cues; each pressure type is reported once
    for words, label in ((("urgent",), "pressure.urgent"), (("bloqu", "blocked"), "pressure.block"),
                         (("suspendu", "suspended"), "pressure.suspend"),
                         (("24h", "24 hours"), "pressure.deadline")):
        if any(word in lower for word in words):
            add(tr(lang, "pressure", label=tr(lang, label)))
    for word in ("code pin", "mot de passe", "otp", "code secret", "identifiant", "password", "pin code"):
        if word in lower:
            add(tr(lang, "secret_request", word=word))
            score += 10
    for word in ("frais de dossier", "frais d'inscription", "envoyez", "réclamer", "reclamer",
                 "processing fee", "registration fee"):
        if word in lower:
            add(tr(lang, "advance_fee", word=word))
            score += 20
            break

    sender_check = check_domain(msg.sender_domain, whitelist)
    if sender_check["status"] == "whitelisted":
        facts["sender_whitelisted"] = True
        add(tr(lang, "official_sender", institution=sender_check['institution'], domain=msg.sender_domain), True)
    elif sender_check["status"] in ("lookalike", "brand_impersonation"):
        facts["brand_spoof"] = True
        facts["brand"] = sender_check.get("institution")
        score += 40
        add(tr(lang, "sender_imitates", institution=sender_check['institution'], domain=msg.sender_domain))

    if msg.reply_to_domain and msg.sender_domain and msg.reply_to_domain != msg.sender_domain:
        score += 15
        add(tr(lang, "reply_to_other", domain=msg.reply_to_domain))

    auth = msg.auth_results
    failed = [m.upper() for m, r in auth.items() if r in ("fail", "softfail", "none")]
    if failed:
        score += 20
        add(tr(lang, "auth_failed", methods=', '.join(failed)))
    facts["auth_pass"] = bool(auth) and all(r == "pass" for r in auth.values())

    risky_ext = (".exe", ".scr", ".js", ".vbs", ".apk", ".bat", ".iso", ".docm", ".xlsm", ".html")
    for att in msg.attachments:
        if att["filename"].lower().endswith(risky_ext):
            score += 30
            add(tr(lang, "dangerous_attachment", filename=att['filename']))

    return min(100, score), evidence, positives, facts


def run_pipeline(text: str | None = None, raw_eml: bytes | None = None, source: str = "web",
                 lang: str = DEFAULT_LANG) -> dict:
    lang = normalize_lang(lang)
    started = time.perf_counter()
    msg = parse_eml(raw_eml) if raw_eml is not None else parse_text(text or "")
    if len(msg.text) < MIN_TEXT_LENGTH:
        raise ParseError("error.too_short")

    whitelist = load_whitelist()  # needs app context -> read before threads
    blocklist = load_blocklist()

    # Email origin (real emails only): needs the app's instance folder for its IP cache
    instance_path = None
    if raw_eml is not None:
        try:
            from flask import current_app
            instance_path = current_app.instance_path
        except RuntimeError:
            pass

    # The AI call is the slow part (network); run everything in parallel
    with ThreadPoolExecutor(max_workers=4) as pool:
        origin_future = pool.submit(_trace_origin, raw_eml, instance_path) if raw_eml is not None else None
        ai_future = pool.submit(analyze_with_ai, msg.text, lang)
        ml_future = pool.submit(_ml_signal, msg.text)
        url_future = pool.submit(analyze_urls, msg.urls, whitelist, lang, blocklist)
        rules_score, rules_evidence, rules_positive, facts = _rules_signal(msg, whitelist, lang)
        ai_verdict, ml_score, url_intel = ai_future.result(), ml_future.result(), url_future.result()
        origin = origin_future.result() if origin_future else None

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
    }, facts, lang)

    evidence, positives = list(rules_evidence), list(rules_positive)
    for r in url_intel["results"]:
        evidence.extend(f"{reason} — {r['host']}" for reason in r["reasons"])
    brand = facts.get("brand") or next(
        (r["domain"].get("institution") for r in url_intel["results"]
         if r["domain"]["status"] in ("lookalike", "brand_impersonation")), None)
    if origin:
        # "Claims to be MTN, sent from abroad" needs the brand, known only now
        if brand and (origin.get("geo") or {}).get("country_code") not in (None, "CM"):
            origin["flags"].append("foreign_for_local_brand")
        origin["claimed_brand"] = brand
        geo = origin.get("geo") or {}
        for flag in origin["flags"]:
            if flag in ORIGIN_EVIDENCE:
                evidence.append(tr(lang, f"origin.{flag}", country=geo.get("country") or "?",
                                   brand=brand or "", provider=origin.get("provider") or ""))
    if ai_verdict:
        evidence.extend(tr(lang, "ai_prefix", reason=reason) for reason in ai_verdict.reasons)
    positives += [False] * (len(evidence) - len(positives))

    return {
        **fused,
        "evidence": evidence,
        "evidence_positive": positives,
        "lang": lang,
        "ai": ai_verdict.model_dump() if ai_verdict else None,
        "ai_model": AI_MODEL if ai_verdict else None,
        "urls": url_intel["results"],
        # Institution the message pretends to be (drives the "official contact" advice)
        "brand": brand,
        # Where the email was really sent from (admin: full report; users: email_origin.public_view)
        "origin": origin,
        "message": {
            "source": source,
            "type": msg.source_type,
            "subject": msg.subject,
            "sender": msg.sender,
            "sender_domain": msg.sender_domain,
            "auth_results": msg.auth_results,
            "attachments": msg.attachments,
        },
        "recommendation": ai_verdict.recommendation if ai_verdict else tr(lang, "default_recommendation"),
        "duration_ms": round((time.perf_counter() - started) * 1000),
    }