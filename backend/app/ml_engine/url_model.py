"""
XGBoost-based URL classifier.

Interface mirrors NaiveBayesClassifier for consistency:
    train(urls, labels)
    predict_proba(url)
    save(path)
    load(path)

No scikit-learn dependency — uses xgboost.XGBClassifier directly.
"""

from __future__ import annotations

import os
from typing import Sequence

import joblib
import numpy as np
import xgboost as xgb

from .url_features import (
    FEATURE_NAMES,
    NUM_FEATURES,
    extract_url_features,
)


class URLClassifier:
    """Binary classifier: 1 = phishing/malicious, 0 = legitimate."""

    def __init__(self, n_estimators: int = 300, max_depth: int = 6, learning_rate: float = 0.1):
        self.params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "tree_method": "hist",
            "random_state": 42,
            "n_jobs": -1,
        }
        self.model: xgb.XGBClassifier | None = None
        self.feature_names = list(FEATURE_NAMES)

    # ------------------------------------------------------------------ train
    def train(self, urls: Sequence[str], labels: Sequence[int]) -> None:
        if len(urls) != len(labels) or not urls:
            raise ValueError("urls and labels must have the same non-zero length")
        if set(labels) != {0, 1}:
            raise ValueError("labels must contain both 0 (legit) and 1 (phishing)")

        X = self._featurize(urls)
        y = np.array(labels, dtype=np.int32)

        self.model = xgb.XGBClassifier(**self.params)
        self.model.fit(X, y, verbose=False)

    # --------------------------------------------------------------- predict
    def predict_proba(self, url: str) -> float:
        """Return probability that the URL is malicious (0.0 to 1.0)."""
        if self.model is None:
            raise RuntimeError("URLClassifier must be trained before prediction")
        features = extract_url_features(url).reshape(1, -1)
        proba = self.model.predict_proba(features)[0, 1]
        return float(proba)

    def predict_proba_batch(self, urls: Sequence[str]) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("URLClassifier must be trained before prediction")
        X = self._featurize(urls)
        return self.model.predict_proba(X)[:, 1]

    # --------------------------------------------------------------- persist
    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "feature_names": self.feature_names,
                "params": self.params,
            },
            path,
        )

    @classmethod
    def load(cls, path: str) -> "URLClassifier":
        payload = joblib.load(path)
        instance = cls(
            n_estimators=payload["params"]["n_estimators"],
            max_depth=payload["params"]["max_depth"],
            learning_rate=payload["params"]["learning_rate"],
        )
        instance.model = payload["model"]
        instance.feature_names = payload["feature_names"]
        return instance

    # --------------------------------------------------------------- helpers
    @staticmethod
    def _featurize(urls: Sequence[str]) -> np.ndarray:
        return np.vstack([extract_url_features(u) for u in urls]).astype(np.float32)

    def feature_importance(self) -> dict[str, float]:
        """Return a dict mapping feature name to normalized importance."""
        if self.model is None:
            return {}
        raw = self.model.feature_importances_
        total = float(raw.sum()) or 1.0
        return {name: float(v / total) for name, v in zip(self.feature_names, raw)}