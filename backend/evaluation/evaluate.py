"""
Measure PhishGuard's accuracy on held-out data (never used for training).

    python evaluation/evaluate.py            # offline: ML, rules, URL and the fused pipeline without AI
    python evaluation/evaluate.py --ai 60    # + the full pipeline WITH Claude on up to 60 local test messages

For each configuration: precision, recall, F1, false-positive rate, confusion matrix and
latency, per source (synthetic templates held out, hand-written challenge set, admin labels,
UCI SMS sample). "Flagged" = the platform warns the user (Medium or above, score > 40).
Writes docs/evaluation/results.json + results.md and instance/evaluation.json (admin page).
"""
from __future__ import annotations

import csv
import json
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
CORPUS = os.path.join(BACKEND, 'ml_data', 'corpus.csv')
DOCS = os.path.join(os.path.dirname(BACKEND), 'docs', 'evaluation')
UCI_SAMPLE = 300


def score_metrics(pairs: list[tuple[int, float]], threshold: float) -> dict:
    tp = sum(1 for y, s in pairs if y == 1 and s > threshold)
    fn = sum(1 for y, s in pairs if y == 1 and s <= threshold)
    fp = sum(1 for y, s in pairs if y == 0 and s > threshold)
    tn = sum(1 for y, s in pairs if y == 0 and s <= threshold)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {'n': len(pairs), 'precision': round(precision, 4), 'recall': round(recall, 4),
            'f1': round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
            'false_positive_rate': round(fp / (fp + tn), 4) if fp + tn else None,
            'accuracy': round((tp + tn) / len(pairs), 4) if pairs else None,
            'confusion': {'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn}}


def main():
    ai_budget = int(sys.argv[sys.argv.index('--ai') + 1]) if '--ai' in sys.argv else 0
    with open(CORPUS, encoding='utf-8') as fh:
        rows = [r for r in csv.DictReader(fh) if r['split'] == 'test']
    rng = random.Random(42)
    uci = [r for r in rows if r['source'] == 'uci_sms']
    local = [r for r in rows if r['source'] != 'uci_sms']
    sample = local + rng.sample(uci, min(UCI_SAMPLE, len(uci)))
    print(f'Evaluating {len(sample)} held-out messages ({len(local)} local + {len(sample) - len(local)} UCI)')

    from app import create_app
    app = create_app()
    api_key = os.environ.pop('ANTHROPIC_API_KEY', None)  # offline run first: no AI
    results: dict = {}
    per: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    latencies = []
    skipped = 0
    with app.app_context():
        from app.pipeline import ParseError, run_pipeline
        for i, r in enumerate(sample, 1):
            label, source = int(r['label']), r['source']
            started = time.perf_counter()
            try:
                out = run_pipeline(text=r['text'], lang='fr')
            except ParseError:  # under 10 characters: the platform refuses to analyse it
                skipped += 1
                continue
            latencies.append((time.perf_counter() - started) * 1000)
            s = out['signals']
            for config, value in (('ml_only', s.get('ml')), ('rules_only', s.get('rules')),
                                  ('pipeline_no_ai', out['score'])):
                if value is not None:
                    for key in (source, 'all_local' if source != 'uci_sms' else 'uci', 'all'):
                        per[config][key].append((label, float(value)))
            if i % 100 == 0:
                print(f'  {i}/{len(sample)}')

        if ai_budget and api_key:
            os.environ['ANTHROPIC_API_KEY'] = api_key
            ai_rows = rng.sample(local, min(ai_budget, len(local)))
            print(f'With AI on {len(ai_rows)} local messages...')
            for r in ai_rows:
                started = time.perf_counter()
                out = run_pipeline(text=r['text'], lang='fr')
                per['pipeline_with_ai']['ai_latency_ms'].append((0, (time.perf_counter() - started) * 1000))
                per['pipeline_with_ai'][r['source']].append((int(r['label']), out['score']))
                per['pipeline_with_ai']['all_local'].append((int(r['label']), out['score']))
                if out['signals'].get('ai') is not None:
                    per['ai_only']['all_local'].append((int(r['label']), out['signals']['ai']))

    for config, groups in per.items():
        results[config] = {}
        for key, pairs in groups.items():
            if key == 'ai_latency_ms':
                continue
            results[config][key] = {'flagged': score_metrics(pairs, 40), 'phishing': score_metrics(pairs, 60)}
    ai_lat = [v for _, v in per.get('pipeline_with_ai', {}).get('ai_latency_ms', [])]
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'test_messages': len(sample) - skipped,
        'skipped_too_short': skipped,
        'latency_ms': {'offline_p50': round(sorted(latencies)[len(latencies) // 2]),
                       'offline_p95': round(sorted(latencies)[int(len(latencies) * 0.95)]),
                       'with_ai_p50': round(sorted(ai_lat)[len(ai_lat) // 2]) if ai_lat else None},
        'definitions': {'flagged': 'score > 40 (suspicious or phishing: the user is warned)',
                        'phishing': 'score > 60 (High or Critical)'},
        'results': results,
    }
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, 'results.json'), 'w', encoding='utf-8') as fh:
        json.dump(report, fh, indent=2)
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        with open(os.path.join(app.instance_path, 'evaluation.json'), 'w', encoding='utf-8') as fh:
            json.dump(report, fh)

    lines = ['# PhishGuard-AI - evaluation on held-out data', '',
             f"Generated {report['generated_at']} on {len(sample)} messages never used for training.", '',
             '| Configuration | Test set | n | Precision | Recall | F1 | False-positive rate |', '|---|---|---|---|---|---|---|']
    for config, groups in results.items():
        for key, m in sorted(groups.items()):
            f = m['flagged']
            lines.append(f"| {config} | {key} | {f['n']} | {f['precision']:.2f} | {f['recall']:.2f} | {f['f1']:.2f} | {f['false_positive_rate']} |")
    with open(os.path.join(DOCS, 'results.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
