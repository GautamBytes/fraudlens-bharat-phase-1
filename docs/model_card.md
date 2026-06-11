# Phase 1 Model And Data Card

## Model Name

FraudLens Bharat Phase 1 Hybrid Baseline

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

The classifier uses TF-IDF features and Logistic Regression.

The model text includes transparent domain markers generated from documented fraud indicators.

The API also includes a rule-only fallback when model files are unavailable.

## Labels

- `kyc_scam`
- `digital_arrest`
- `fake_job`
- `investment_scam`
- `loan_scam`
- `courier_scam`
- `upi_refund_scam`
- `otp_phishing`

## Dataset

| Item | Value |
|---|---:|
| Dataset file | `data/samples/phase1_seed_dataset.csv` |
| Rows | 64 |
| Classes | 8 |
| Rows per class | 8 |
| Data source | Synthetic, educational seed examples |
| Real PII | Not required |

## Current Metrics

| Model | Accuracy | Macro F1 | Test Rows |
|---|---:|---:|---:|
| Rule-only fallback | 0.8125 | 0.7833 | 16 |
| Hybrid baseline | 1.0000 | 1.0000 | 16 |

These are internal synthetic metrics. They do not prove real-world generalization.

## Known Limitations

- Dataset is small and synthetic.
- Test support is only two examples per class.
- Real cyber-fraud messages may contain more noise, spelling variation, code-mixing, screenshots, and missing context.
- The model does not inspect images, attachments, voice notes, or transactions.
- The URL module is heuristic and not a trained phishing URL classifier.

## Safety Notes

Use dummy examples for demos.

Do not store real phone numbers, account numbers, UPI IDs, names, or screenshots in Phase 1.

The complaint draft is an assistive summary. The user must manually review and report through official channels when appropriate.

## Maintenance

When new data is added, retrain the baseline, inspect the confusion matrix, update `models/metrics.json`, and add regression tests for repeated errors.
