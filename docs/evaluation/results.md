# PhishGuard-AI - evaluation on held-out data

Generated 2026-09-26T09:57:34.826758+00:00 on 504 messages never used for training.

| Configuration | Test set | n | Precision | Recall | F1 | False-positive rate |
|---|---|---|---|---|---|---|
| ml_only | admin | 2 | 1.00 | 1.00 | 1.00 | None |
| ml_only | all | 501 | 0.83 | 0.99 | 0.90 | 0.0838 |
| ml_only | all_local | 204 | 0.78 | 0.99 | 0.88 | 0.3191 |
| ml_only | challenge | 24 | 0.85 | 0.92 | 0.88 | 0.1667 |
| ml_only | synthetic | 178 | 0.77 | 1.00 | 0.87 | 0.3415 |
| ml_only | uci | 297 | 1.00 | 1.00 | 1.00 | 0.0 |
| ml_only | uci_sms | 297 | 1.00 | 1.00 | 1.00 | 0.0 |
| rules_only | admin | 2 | 1.00 | 0.50 | 0.67 | None |
| rules_only | all | 501 | 1.00 | 0.06 | 0.11 | 0.0 |
| rules_only | all_local | 204 | 1.00 | 0.06 | 0.12 | 0.0 |
| rules_only | challenge | 24 | 0.00 | 0.00 | 0.00 | 0.0 |
| rules_only | synthetic | 178 | 1.00 | 0.06 | 0.12 | 0.0 |
| rules_only | uci | 297 | 1.00 | 0.03 | 0.06 | 0.0 |
| rules_only | uci_sms | 297 | 1.00 | 0.03 | 0.06 | 0.0 |
| pipeline_no_ai | admin | 2 | 1.00 | 0.50 | 0.67 | None |
| pipeline_no_ai | all | 501 | 0.92 | 0.84 | 0.88 | 0.0279 |
| pipeline_no_ai | all_local | 204 | 0.90 | 0.81 | 0.85 | 0.1064 |
| pipeline_no_ai | challenge | 24 | 0.88 | 0.58 | 0.70 | 0.0833 |
| pipeline_no_ai | synthetic | 178 | 0.90 | 0.84 | 0.87 | 0.1098 |
| pipeline_no_ai | uci | 297 | 1.00 | 0.94 | 0.97 | 0.0 |
| pipeline_no_ai | uci_sms | 297 | 1.00 | 0.94 | 0.97 | 0.0 |
| pipeline_with_ai | admin | 1 | 0.00 | 0.00 | 0.00 | None |
| pipeline_with_ai | all_local | 40 | 0.92 | 0.96 | 0.94 | 0.125 |
| pipeline_with_ai | challenge | 5 | 1.00 | 1.00 | 1.00 | 0.0 |
| pipeline_with_ai | synthetic | 34 | 0.91 | 1.00 | 0.95 | 0.1429 |
| ai_only | all_local | 40 | 0.92 | 1.00 | 0.96 | 0.125 |
