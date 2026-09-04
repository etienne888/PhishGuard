import re
from urllib.parse import urlparse


class HeuristicScorer:
    """Score common phishing signals on a 0-100 scale."""

    _urgent_terms = {
        "urgent", "urgence", "immediat", "immediate", "bloque", "suspendu",
        "confirmez", "verifiez", "verification", "mot de passe", "code pin",
    }
    _money_terms = {"momo", "mobile money", "orange money", "fcfa", "gagne", "envoyez"}

    def score(self, text, sender_domain=None):
        normalized = text.lower()
        score = 0

        score += min(30, sum(normalized.count(term) for term in self._urgent_terms) * 10)
        score += min(25, sum(normalized.count(term) for term in self._money_terms) * 5)
        score += min(25, len(re.findall(r"https?://|www\.", normalized)) * 25)
        score += min(10, normalized.count("!") * 5)

        if sender_domain and self._looks_suspicious_domain(sender_domain):
            score += 15

        return min(100, score)

    @staticmethod
    def _looks_suspicious_domain(domain):
        parsed = urlparse(domain if "://" in domain else f"https://{domain}")
        hostname = (parsed.hostname or "").lower()
        return any(hostname.endswith(tld) for tld in (".tk", ".ga", ".ml", ".cf", ".gq"))
