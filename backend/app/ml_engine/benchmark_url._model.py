"""
Benchmark the trained URL model on a fixed test set.

Usage:
    python backend/scripts/benchmark_url_model.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml_engine.url_model import URLClassifier  # noqa: E402
from app.ml_engine.train_url import compute_metrics, print_metrics  # noqa: E402


BENCHMARK = [
    # (url, is_malicious_ground_truth)
    # --- Known phishing patterns ---
    ("http://mtn-secure.tk/verify", 1),
    ("http://orange-verify.ga/login", 1),
    ("http://afriland-secure.cf/account", 1),
    ("http://192.168.1.1/admin", 1),
    ("http://xn--80ak6aa92e.com/login", 1),
    ("http://paypal-secure-update.top/signin", 1),
    ("http://bit.ly/phish123", 1),
    ("http://apple-icloud-verify.ml/account", 1),
    ("http://whatsapp-verify.xyz/confirm", 1),
    ("http://camtel-promo.cf/free", 1),
    ("http://mtnn-secure.com/login", 1),          # brand lookalike
    ("http://user@evil.com/verify", 1),           # @ trick
    ("http://example.com/%2e%2e/admin", 1),       # hex escape
    ("http://amazon-billing-update.work/signin", 1),
    ("http://facebook-security-check.click/login", 1),
    # --- Known legitimate patterns ---
    ("https://www.google.com", 0),
    ("https://www.orange.cm", 0),
    ("https://www.mtn.cm", 0),
    ("https://www.camtel.cm", 0),
    ("https://www.afrilandfirstbank.com", 0),
    ("https://github.com/login", 0),
    ("https://www.wikipedia.org", 0),
    ("https://www.gov.cm/services", 0),
    ("https://www.youtube.com/watch?v=abc", 0),
    ("https://www.linkedin.com/in/user", 0),
]


def main():
    model_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "ml_engine", "trained", "url_model.pkl"
    )
    model_path = os.path.abspath(model_path)

    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
        print("Run: python -m app.ml_engine.train_url")
        sys.exit(1)

    print(f"Loading model from {model_path}")
    model = URLClassifier.load(model_path)

    urls = [u for u, _ in BENCHMARK]
    truths = [label for _, label in BENCHMARK]
    probas = model.predict_proba_batch(urls)
    preds = (probas >= 0.5).astype(int)

    print("\nPer-URL predictions:")
    for (url, truth), proba, pred in zip(BENCHMARK, probas, preds):
        status = "✓" if pred == truth else "✗"
        print(f"  {status} {proba*100:6.2f}%  truth={truth}  {url}")

    import numpy as np
    m = compute_metrics(np.array(truths), preds)
    print_metrics("Benchmark", m)


if __name__ == "__main__":
    main()