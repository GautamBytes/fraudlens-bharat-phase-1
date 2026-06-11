# Evaluation Plan

## Purpose

This plan defines how to evaluate FraudLens Bharat without overstating the Phase 1 result.

It separates classification accuracy from extraction quality, risk usefulness, system behavior, and safety.

## Current Phase 1 Dataset

| Item | Value |
|---|---:|
| Total rows | 64 |
| Train rows | 48 |
| Test rows | 16 |
| Fraud classes | 8 |
| Rows per class | 8 |
| Test rows per class | 2 |
| Data type | Synthetic, manually reviewed seed examples |

The dataset is intentionally small. Its purpose is to prove the pipeline and establish a measurable baseline.

## Classification Metrics

Classification should be measured with:

- Accuracy
- Macro precision
- Macro recall
- Macro F1
- Per-class precision, recall, and F1
- Confusion matrix

Macro F1 is the main Phase 1 classifier metric because every fraud class matters equally.

## Current Classification Result

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---:|---:|---:|---:|
| Rule-only fallback | 0.8125 | 0.7917 | 0.8125 | 0.7833 |
| Hybrid TF-IDF baseline | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

The hybrid result is based on the current 16-row synthetic test split. It should be reported with this limitation every time.

## Extraction Metrics

Entity extraction should be evaluated separately from classification.

Recommended labels:

- `phone`
- `url`
- `upi_id`
- `email`
- `money`
- `otp_like_code`
- `urgency_phrase`
- `threat_phrase`

Recommended metrics:

- Entity precision by type
- Entity recall by type
- Exact-match accuracy for normalized phone, URL, email, UPI ID, and OTP values
- Manual review notes for ambiguous phrases

## Current Extraction Checks

Automated tests already cover phone, URL, UPI ID, email, money, OTP-like code, urgency phrase, and threat phrase extraction.

Regression tests also check that an email is not partially extracted as a UPI ID and that contextual bare amounts like "Invest 5000" are extracted.

## Risk Scoring Metrics

Risk scoring should not be evaluated only by accuracy because risk labels are partly policy choices.

Use these checks:

- Low-risk control examples stay below 35
- Medium-risk examples fall between 35 and 69.99
- High-risk examples reach 70 or above
- Each high-risk result includes at least two visible reasons
- URL and OTP cases include the expected risk signals

## Complaint Draft Quality

Complaint draft quality should be manually reviewed using a checklist.

The draft should include:

- Suspected fraud type
- Risk level
- Extracted entities
- Original message
- Manual action guidance
- No automatic submission claim
- No request for unnecessary private data

## System Metrics

Recommended system metrics:

- API health endpoint returns `ok`
- `/analyze` returns a complete schema
- `/cases` stores and lists analyzed cases
- Dashboard loads demo messages
- Baseline model training regenerates metrics and confusion matrix
- Test suite passes

Phase 1 can report these as reproducibility metrics.

## Accuracy Maintenance Rules

When new seed data is added:

1. Keep class balance visible.
2. Re-run `python -m fraudlens.model_training`.
3. Compare macro-F1 with the prior baseline.
4. Inspect the confusion matrix, not only the headline score.
5. Add regression tests for any recurring confusion.
6. Avoid hiding weak results; document them as Phase 2 targets.

## Phase 2 Evaluation Targets

Phase 2 should use a larger mixed-language dataset and add external validation if possible.

Recommended targets:

- At least 200 examples per class before claiming robust classifier quality
- OCR extraction accuracy for screenshot inputs
- Transformer comparison against TF-IDF baseline
- URL model comparison against URL heuristics
- Graph-linking evaluation for repeated phone, UPI, email, and URL identifiers
- Latency measurement for API and dashboard demos

## Reporting Rule

The main report should state: "The current Phase 1 result is an internal synthetic benchmark and not a claim of production accuracy."

That sentence protects the project while still showing measurable progress.
