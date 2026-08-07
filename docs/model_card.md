# Phase 1 Model And Data Card

## Model Name

FraudLens Bharat calibrated TF-IDF bootstrap predictor

## Intended Use

The model supports demo-stage cyber-fraud triage for pasted SMS or WhatsApp-style text.

It predicts a likely fraud category and feeds the result into entity extraction, URL risk analysis, scoring, and complaint-draft generation.

## Not Intended For

- Automatic police complaint submission
- Legal decision-making
- Real victim profiling
- Production fraud blocking
- Use on private victim data without consent and privacy controls

## Model Type

The selected classifier uses raw-normalized TF-IDF features, Logistic Regression, and sigmoid calibration.

It applies a threshold selected on the frozen validation split and abstains as `unknown` below that threshold.

The API uses a rule-only fallback only when persisted artifacts are unavailable or corrupt; weak generic keyword matches abstain.

## Labels

- `kyc_scam`
- `digital_arrest`
- `fake_job`
- `investment_scam`
- `loan_scam`
- `courier_scam`
- `upi_refund_scam`
- `otp_phishing`

`legitimate` remains a supported prediction-boundary label, but is absent from the current bootstrap and was not fabricated for training.

## Dataset

| Item | Value |
|---|---:|
| Dataset file | `data/samples/phase2_dataset.csv` |
| Rows | 64 |
| Classes | 8 |
| Rows per class | 8 |
| Splits | 48 train / 8 validation / 8 frozen test |
| Data source | Synthetic, educational bootstrap examples |
| Real PII | Not required |

## Current Metrics

| Model | Overall accuracy | Raw macro F1 | Coverage | Abstention | Accepted accuracy | Frozen test rows |
|---|---:|---:|---:|---:|---:|---:|
| Calibrated raw-normalized TF-IDF | 0.5000 | 0.5000 | 87.5% | 12.5% | 57.14% | 8 |

These are internal synthetic bootstrap metrics. The target is unmet: no legitimate examples are available and every label is well below the 200-example target. They do not prove real-world generalization or production readiness.

## Known Limitations

- Dataset is small, synthetic, and has no legitimate examples.
- Frozen test support is one example per fraud class.
- Real cyber-fraud messages may contain more noise, spelling variation, code-mixing, screenshots, and missing context.
- The model does not inspect images, attachments, voice notes, or transactions.
- The URL module is heuristic and not a trained phishing URL classifier.

## Safety Notes

Use dummy examples for demos.

Do not store real phone numbers, account numbers, UPI IDs, names, or screenshots in Phase 1.

The complaint draft is an assistive summary. The user must manually review and report through official channels when appropriate.

## Maintenance

When new data is added, retrain the baseline, inspect the confusion matrix, update `models/metrics.json`, and add regression tests for repeated errors.
