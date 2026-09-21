"""
Training script for the URL classifier.

Usage:
    python -m app.ml_engine.train_url

Downloads:
    - URLhaus (malicious URLs)
    - Tranco Top 1M (legitimate URLs)

Then extracts features, splits train/test, trains XGBoost, evaluates
on the holdout set, and saves the model.
"""

from __future__ import annotations

import csv
import io
import os
import random
import sys
import urllib.request
import zipfile
from datetime import datetime

import numpy as np

from .url_features import extract_url_features
from .url_model import URLClassifier


# ---------------------------------------------------------------------------
# Dataset URLs
# ---------------------------------------------------------------------------

URLHAUS_CSV = "https://urlhaus.abuse.ch/downloads/csv_recent/"
TRANCO_ZIP = "https://tranco-list.eu/download_daily/PLACEHOLDER"  # see note below

# Fallback: if Tranco download fails, use a small curated legitimate list
FALLBACK_LEGIT = [
    "https://www.google.com",
    "https://www.facebook.com",
    "https://www.youtube.com",
    "https://www.wikipedia.org",
    "https://www.orange.cm",
    "https://www.mtn.cm",
    "https://www.camtel.cm",
    "https://www.afrilandfirstbank.com",
    "https://www.gov.cm",
    "https://www.presidenceducameroun.cm",
]


# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------

def _download(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "PhishGuard-AI/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def fetch_urlhaus(limit: int = 20000) -> list[str]:
    """Download and parse URLhaus recent CSV. Returns list of malicious URLs."""
    print(f"Downloading URLhaus ({limit} max)...")
    try:
        raw = _download(URLHAUS_CSV).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  URLhaus download failed: {e}")
        return []

    urls: list[str] = []
    # URLhaus CSV format: id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter
    for line in raw.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        try:
            row = next(csv.reader([line]))
            if len(row) >= 3:
                candidate = row[2].strip()
                if candidate.startswith("http"):
                    urls.append(candidate)
                    if len(urls) >= limit:
                        break
        except Exception:
            continue

    print(f"  Fetched {len(urls)} malicious URLs")
    return urls


def fetch_tranco_legit(limit: int = 20000) -> list[str]:
    """
    Download Tranco list and turn top domains into https URLs.

    Note: Tranco changes the download URL daily. We try the latest known
    endpoints; if all fail, we fall back to a curated list.
    """
    # Tranco doesn't have a stable direct-download URL. We try a well-known
    # mirror; if it fails, we use the fallback list.
    try:
        print("Downloading Tranco Top 1M (this may take a minute)...")
        raw = _download("https://tranco-list.eu/top-1m.csv.zip", timeout=60)
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            name = zf.namelist()[0]
            content = zf.read(name).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  Tranco download failed: {e}")
        print("  Using fallback legitimate list.")
        return FALLBACK_LEGIT[:limit]

    urls: list[str] = []
    for line in content.splitlines():
        parts = line.split(",")
        if len(parts) >= 2:
            domain = parts[1].strip()
            if domain:
                urls.append(f"https://{domain}")
                if len(urls) >= limit:
                    break
    print(f"  Fetched {len(urls)} legitimate URLs")
    return urls


# ---------------------------------------------------------------------------
# Train / test split (no sklearn)
# ---------------------------------------------------------------------------

def train_test_split(
    urls: list[str],
    labels: list[int],
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple[list[str], list[str], list[int], list[int]]:
    rng = random.Random(seed)
    indices = list(range(len(urls)))
    rng.shuffle(indices)
    split = int(len(urls) * (1 - test_size))
    train_idx = indices[:split]
    test_idx = indices[split:]
    return (
        [urls[i] for i in train_idx],
        [urls[i] for i in test_idx],
        [labels[i] for i in train_idx],
        [labels[i] for i in test_idx],
    )


# ---------------------------------------------------------------------------
# Metrics (no sklearn)
# ---------------------------------------------------------------------------

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / max(tp + tn + fp + fn, 1)

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def print_metrics(name: str, m: dict) -> None:
    print(f"\n=== {name} ===")
    print(f"  Accuracy:  {m['accuracy']:.4f}")
    print(f"  Precision: {m['precision']:.4f}")
    print(f"  Recall:    {m['recall']:.4f}")
    print(f"  F1:        {m['f1']:.4f}")
    print(f"  Confusion: TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def train_url_model() -> None:
    print("=" * 60)
    print("PhishGuard-AI — URL classifier training")
    print("=" * 60)

    # 1. Fetch data
    malicious = fetch_urlhaus(limit=15000)
    legit = fetch_tranco_legit(limit=15000)

    if len(malicious) < 100 or len(legit) < 100:
        print("Not enough training data. Aborting.")
        sys.exit(1)

    # 2. Combine + label
    urls = malicious + legit
    labels = [1] * len(malicious) + [0] * len(legit)
    print(f"\nTotal dataset: {len(urls)} ({len(malicious)} malicious, {len(legit)} legit)")

    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(urls, labels, test_size=0.2)
    print(f"Train: {len(X_train)}  Test: {len(X_test)}")

    # 4. Train
    print("\nTraining XGBoost classifier...")
    model = URLClassifier(n_estimators=300, max_depth=6, learning_rate=0.1)
    model.train(X_train, y_train)

    # 5. Evaluate on holdout
    print("Evaluating on test set...")
    proba = model.predict_proba_batch(X_test)
    pred = (proba >= 0.5).astype(int)
    metrics = compute_metrics(np.array(y_test), pred)
    print_metrics("URL model — holdout", metrics)

    # 6. Feature importance
    print("\nTop 10 features by importance:")
    importance = model.feature_importance()
    for name, value in sorted(importance.items(), key=lambda x: -x[1])[:10]:
        print(f"  {name:<28} {value:.4f}")

    # 7. Save
    model_dir = os.path.join(os.path.dirname(__file__), "trained")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "url_model.pkl")
    model.save(model_path)
    print(f"\nModel saved to {model_path}")
    print(f"Trained at {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    train_url_model()