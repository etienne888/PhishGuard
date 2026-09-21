"""
Hybrid detector: Naive Bayes (text) + URL classifier (XGBoost) + heuristics.

Backward compatible with the previous version:
  - Same constructor
  - Same analyze(text, sender_domain) signature
  - Same return dict keys plus new optional URL fields
"""

import os

from .model_manager import NaiveBayesClassifier
from .heuristic_scorer import HeuristicScorer
from .url_features import extract_urls_from_text


class HybridDetector:
    def __init__(self):
        # Text-level model (existing)
        self.ml_model = NaiveBayesClassifier()
        text_model_path = os.path.join(
            os.path.dirname(__file__), "trained", "classifier.joblib"
        )
        try:
            self.ml_model = self.ml_model.load(text_model_path)
            print("ML model loaded successfully.")
        except FileNotFoundError:
            print("ML model not trained yet; text analysis unavailable.")

        # URL-level model (new — optional)
        self.url_model = None
        url_model_path = os.path.join(
            os.path.dirname(__file__), "trained", "url_model.pkl"
        )
        try:
            from .url_model import URLClassifier
            self.url_model = URLClassifier.load(url_model_path)
            print("URL model loaded successfully.")
        except FileNotFoundError:
            print("URL model not trained yet; URL analysis disabled.")
        except Exception as e:
            print(f"URL model load failed ({e}); URL analysis disabled.")

        self.heuristic = HeuristicScorer()

    def analyze(self, text, sender_domain=None):
        # 1. Text model — Naive Bayes
        try:
            ml_prob = self.ml_model.predict_proba(text)
            ml_score = ml_prob * 100
        except Exception:
            ml_score = 0.0

        # 2. Heuristic scorer
        heuristic_score = self.heuristic.score(text, sender_domain)

        # 3. URL analysis — extract every URL and classify each
        url_score = 0.0
        url_verdict = "unknown"
        url_indicators = []
        urls = extract_urls_from_text(text)
        if urls and self.url_model is not None:
            scores = []
            for url in urls:
                try:
                    p = self.url_model.predict_proba(url)
                    scores.append(p)
                    if p >= 0.5:
                        url_indicators.append(
                            f"URL suspecte ({p*100:.0f}%) : {url}"
                        )
                except Exception:
                    continue
            if scores:
                url_score = max(scores) * 100  # worst URL wins
                if url_score >= 80:
                    url_verdict = "malicious"
                elif url_score >= 50:
                    url_verdict = "suspicious"
                else:
                    url_verdict = "clean"

        # 4. Weighted fusion
        #    If URL model is unavailable, redistribute its weight to ML+heuristics.
        if self.url_model is not None and urls:
            final_score = (
                ml_score * 0.35
                + url_score * 0.45
                + heuristic_score * 0.20
            )
        else:
            final_score = ml_score * 0.60 + heuristic_score * 0.40

        # 5. Verdict
        if final_score > 80:
            verdict = "Critical"
        elif final_score > 60:
            verdict = "High"
        elif final_score > 40:
            verdict = "Medium"
        else:
            verdict = "Low"

        result = {
            "score": round(final_score, 2),
            "verdict": verdict,
            "ml_score": round(ml_score, 2),
            "heuristic_score": round(heuristic_score, 2),
            "indicators": self._get_indicators(text, sender_domain, url_indicators),
        }
        # Optional, non-breaking additions
        if self.url_model is not None and urls:
            result["url_score"] = round(url_score, 2)
            result["url_verdict"] = url_verdict
        return result

    def _get_indicators(self, text, sender_domain, url_indicators=None):
        """Return a list of human-readable warning strings."""
        indicators = []
        text_lower = text.lower() if text else ""

        # Keyword-based
        urgency = ["urgent", "immédiat", "immediat", "bloqué", "bloque", "suspendu"]
        for kw in urgency:
            if kw in text_lower:
                indicators.append(f"Terme d'urgence détecté : « {kw} »")

        credential = ["mot de passe", "password", "code pin", "identifiant", "otp"]
        for kw in credential:
            if kw in text_lower:
                indicators.append(f"Demande d'identifiants : « {kw} »")

        money = ["mobile money", "momo", "orange money", "fcfa", "transfert"]
        for kw in money:
            if kw in text_lower:
                indicators.append(f"Contexte financier : « {kw} »")

        # Sender
        if sender_domain and self.heuristic._looks_suspicious_domain(sender_domain):
            indicators.append(f"Domaine expéditeur suspect : {sender_domain}")

        # URLs
        if url_indicators:
            indicators.extend(url_indicators)

        # Cap to avoid overwhelming UI
        return indicators[:10]