"""
Train the text model (signal A of the pipeline) on ml_data/corpus.csv.

    python ml_data/build_dataset.py [--with-db]    # 1. build / refresh the corpus
    python train_ml.py                              # 2. train, evaluate on held-out data, save

Model: TF-IDF words (1-2 grams) + characters (3-5 grams) -> logistic regression
(class-balanced). Cameroonian and human-labelled messages weigh more than the
held-out data. Metrics are computed ONLY on the test split (templates
and messages never seen in training) and saved inside the model file.
Output: app/ml_engine/trained/classifier.joblib
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score  # noqa: E402
from sklearn.pipeline import FeatureUnion, Pipeline  # noqa: E402

from app.ml_engine.model_manager import SklearnTextModel, normalize_text as normalize  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, 'ml_data', 'corpus.csv')
OUT = os.path.join(HERE, 'app', 'ml_engine', 'trained', 'classifier.joblib')
WEIGHT = {'synthetic': 1.0, 'admin': 3.0, 'uci_sms': 1.0}  # tuned on held-out data (see docs)


def build_pipeline() -> Pipeline:
    features = FeatureUnion([
        ('words', TfidfVectorizer(preprocessor=normalize, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ('chars', TfidfVectorizer(preprocessor=normalize, analyzer='char_wb', ngram_range=(3, 5), min_df=2,
                                  sublinear_tf=True, max_features=60000)),
    ])
    return Pipeline([('features', features),
                     ('clf', LogisticRegression(C=1.5, class_weight='balanced', max_iter=2000))])


def metrics(y_true, y_prob, threshold=0.5) -> dict:
    y_pred = [1 if p >= threshold else 0 for p in y_prob]
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    out = {'n': len(y_true), 'positives': int(sum(y_true)), 'precision': round(precision_score(y_true, y_pred, zero_division=0), 4),
           'recall': round(recall_score(y_true, y_pred, zero_division=0), 4), 'f1': round(f1_score(y_true, y_pred, zero_division=0), 4),
           'false_positive_rate': round(fp / (fp + tn), 4) if fp + tn else None,
           'accuracy': round((tp + tn) / len(y_true), 4), 'confusion': {'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn)}}
    if len(set(y_true)) == 2:
        out['roc_auc'] = round(roc_auc_score(y_true, y_prob), 4)
    return out


def main():
    with open(CORPUS, encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    train = [r for r in rows if r['split'] == 'train']
    test = [r for r in rows if r['split'] == 'test']
    print(f'Corpus: {len(rows)} messages ({len(train)} train / {len(test)} test)')

    pipeline = build_pipeline()
    pipeline.fit([r['text'] for r in train], [int(r['label']) for r in train],
                 clf__sample_weight=[WEIGHT.get(r['source'], 1.0) for r in train])

    probs = pipeline.predict_proba([r['text'] for r in test])[:, 1]
    by_source = defaultdict(lambda: ([], []))
    for r, p in zip(test, probs):
        by_source[r['source']][0].append(int(r['label']))
        by_source[r['source']][1].append(float(p))
    results = {'all': metrics([int(r['label']) for r in test], list(probs))}
    for source, (y, p) in by_source.items():
        results[source] = metrics(y, p)
    for name, m in results.items():
        print(f"  {name:10s} n={m['n']:5d}  precision={m['precision']:.3f}  recall={m['recall']:.3f}  "
              f"f1={m['f1']:.3f}  FPR={m['false_positive_rate']}")

    meta = {
        'algorithm': 'TF-IDF (words 1-2 + chars 3-5) + logistic regression',
        'trained_at': datetime.now(timezone.utc).isoformat(),
        'train_size': len(train), 'test_size': len(test),
        'sources': {s: sum(1 for r in rows if r['source'] == s) for s in sorted({r['source'] for r in rows})},
        'test_metrics': results,
    }
    SklearnTextModel(pipeline, meta).save(OUT)
    print(f'Model saved to {OUT}')


if __name__ == '__main__':
    main()
