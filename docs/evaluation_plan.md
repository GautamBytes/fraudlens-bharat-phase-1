# Evaluation Plan

## Purpose

This plan defines how to evaluate FraudLens Bharat without overstating the Phase 1 result.

It separates classification accuracy from extraction quality, risk usefulness, system behavior, and safety.

## Current Calibrated Bootstrap Dataset

| Item | Value |
|---|---:|
| Total rows | 64 |
| Train rows | 48 |
| Validation rows | 8 |
| Frozen test rows | 8 |
| Fraud classes | 8 |
| Rows per class | 8 |
| Frozen test rows per fraud class | 1 |
| Legitimate rows | 0 |
| Data type | Synthetic, manually reviewed bootstrap examples |

The dataset is intentionally small. Its purpose is to prove the pipeline and establish a measurable bootstrap, not production performance. The Phase 2 target is unmet: `legitimate` is absent and no label reaches 200 examples.

## Classification Metrics

Classification should be measured with:

- Accuracy
- Macro precision
- Macro recall
- Macro F1
- Coverage and abstention rate
- Accuracy among accepted predictions
- Per-class precision, recall, and F1
- Confusion matrix

Macro F1 is the main Phase 1 classifier metric because every fraud class matters equally.

## Reproducible Comparison Evidence

Run the following command to regenerate the committed evidence in
`outputs/phase2/evaluation.json` and `outputs/phase2/summary.txt`:

```bash
python -m fraudlens.evaluation --dataset data/samples/phase2_dataset.csv --output outputs/phase2
```

All vectorizers, classifiers, and calibration are fit only on train. Each
TF-IDF model's abstention threshold is selected only on validation, then its
frozen test result is calculated once. The rule-only baseline calls the canonical
runtime fallback for each frozen row and accepts exactly when its label is not
`unknown`; it has no evaluator-selected threshold and no calibrated ECE. The
marker-enhanced variant is an ablation and is not selected for runtime use.
Metrics below are copied from the deterministic evidence output, not
extrapolated beyond this synthetic bootstrap.

| Model | Final accuracy | Final macro F1 | Coverage | Abstention | Accepted accuracy | Frozen test rows |
|---|---:|---:|---:|---:|---:|---:|
| Rule-only runtime fallback | 0.2500 | 0.2500 | 25.0% | 75.0% | 100.00% | 8 |
| Raw-normalized TF-IDF | 0.3750 | 0.3333 | 100.0% | 0.0% | 37.50% | 8 |
| Marker TF-IDF (ablation; not selected) | 0.6250 | 0.6250 | 62.5% | 37.5% | 100.00% | 8 |
| Calibrated raw-normalized TF-IDF | 0.5000 | 0.5000 | 87.5% | 12.5% | 57.14% | 8 |

Headline accuracy, macro metrics, per-class metrics, and confusion matrices use
the final prediction: every rejected TF-IDF result is `unknown`, just like a
runtime-rule abstention. Underlying TF-IDF argmax diagnostics remain separately
available as `raw_prediction_metrics`; they are not mixed into the comparable
headline values. The report also includes ECE where applicable, split row
counts, and a deterministic latency note. Every final confusion matrix includes
an explicit `unknown` column and row. Wall-clock measurements are excluded
because they would make the committed evidence non-reproducible. This is a
synthetic bootstrap result, not a production claim or a 9-class result.

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
- Website loads demo messages
- Calibrated model training regenerates metrics and metadata
- Test suite passes

Phase 1 can report these as reproducibility metrics.

## Accuracy Maintenance Rules

When new seed data is added:

1. Keep class balance visible.
2. Re-run `python -m fraudlens.evaluation --dataset data/samples/phase2_dataset.csv --output outputs/phase2`.
3. Compare raw macro-F1, coverage, abstention, accepted accuracy, ECE, and the confusion matrix with the prior evidence.
4. Inspect the confusion matrix, not only the headline score.
5. Add regression tests for any recurring confusion.
6. Avoid hiding weak results; document them as Phase 2 targets.

## Current Capability And Phase 2 Evaluation Targets

Phase 2 should use a larger mixed-language dataset and add external validation if possible.

The current implementation includes screenshot OCR and basic privacy-safe graph
analytics over explicitly stored, unexpired cases. These implemented capabilities
still require stronger evaluation; the graph does not perform production
fraud-network detection or use a GNN. Transformer comparison and GNN research
remain future work.

Recommended evaluation targets:

- At least 200 examples per class before claiming robust classifier quality
- OCR extraction accuracy for screenshot inputs
- Transformer comparison against TF-IDF baseline
- URL model comparison against URL heuristics
- Graph-linking evaluation for repeated phone, UPI, email, and URL identifiers
- Latency measurement for API and website demos

## Reporting Rule

The main report should state: "The current calibrated result is an internal synthetic bootstrap benchmark, has no legitimate examples, and is not a claim of production accuracy."

That sentence protects the project while still showing measurable progress.
