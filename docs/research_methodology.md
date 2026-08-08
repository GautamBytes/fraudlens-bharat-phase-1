# Research Benchmark Methodology

## Purpose

This protocol makes the FraudLens Bharat comparison reproducible and prevents
the current 64-row synthetic bootstrap from being presented as production
accuracy. It separates results produced on the same frozen dataset from values
reported by papers using different datasets and tasks.

## Experimental unit and split policy

Each CSV row is one experimental unit. The immutable `split` column assigns it
to `train`, `validation`, or `test`.

- `train` is the only split used to fit vocabularies, inverse-document-frequency
  weights, coefficients, and calibration models.
- `validation` is used only to select an abstention threshold.
- `test` is evaluated once after model and threshold choices are fixed.

The dataset contract rejects a `template_group` that crosses splits. The audit
also reports any `provenance_id` used across multiple splits. A shared source is
not automatically leakage, but it warns that all current examples have the same
synthetic origin. Text is normalized before duplicate detection so case and
punctuation variants cannot silently inflate the sample size.

The current dataset has 48 train, 8 validation, and 8 test rows. It contains
eight fraud labels, no legitimate label, and only one test row for each present
label. The target remains at least 200 examples per label, including legitimate
messages, before making a robust classifier-quality claim.

## Candidate models

The same rows and labels are used for every candidate:

1. canonical runtime keyword rules;
2. word TF-IDF (1-2 grams) with balanced Logistic Regression;
3. character TF-IDF (3-5 grams) with balanced Logistic Regression;
4. word-character FeatureUnion with balanced Logistic Regression; and
5. the word-character model with train-only three-fold sigmoid calibration.

The rule system is not fitted. Every trainable candidate uses random seed 42.
The code-mixed-transformer result in the literature is external context, not a
candidate trained on this private project split.

## Why these parameters are compared

| Parameter | Reason for inclusion |
|---|---|
| Accuracy | Familiar fraction of all correct final decisions; easy to interpret but sensitive to imbalance. |
| Macro-F1 | Primary model-quality measure. It gives every fraud label equal weight even when class frequency differs. |
| Balanced accuracy | Mean per-class recall; reveals whether majority labels dominate ordinary accuracy. |
| Per-class precision | Measures false alarms for each category, important when a legitimate message could be labelled fraudulent. |
| Per-class recall | Measures missed cases within each fraud category, important for high-harm scams. |
| Weighted-F1 | Describes sample-weighted performance while remaining distinct from the equal-class Macro-F1 objective. |
| Matthews correlation coefficient | A single correlation-style score that remains informative under class imbalance and multiclass errors. |
| Confusion matrix | Shows the exact direction of errors that headline scores hide. |
| Coverage | Fraction of rows receiving a non-`unknown` decision. |
| Abstention rate | Fraction deliberately rejected as uncertain; it must be shown so selective accuracy cannot hide unserved inputs. |
| Accepted accuracy | Accuracy only among covered rows; interpreted together with Coverage. |
| Expected calibration error | Measures disagreement between confidence and observed correctness across confidence bins. |
| Brier score | Proper probability-quality score that penalizes probability mass assigned to incorrect classes. |
| Estimated model bytes | Deterministic estimate of fitted vocabulary and numerical payload; supports a deployability comparison without non-reproducible serialization metadata. |

Wall-clock latency, peak memory, and energy usage are relevant deployment
parameters, but they are environment dependent. They must be reported with CPU,
operating system, Python version, warm-up count, repetition count, and p50/p95
rather than written into canonical byte-reproducible evidence.

## Selective prediction

For a trainable model, confidence is the highest class probability. Candidate
thresholds come only from validation confidences. The objective counts a
correct accepted prediction as +1, an incorrect accepted prediction as -1, and
an abstention as 0; ties favour higher Coverage. A final abstention is recorded
as `unknown` and counts as an error in overall accuracy and Macro-F1.

The rule system accepts only when the canonical runtime fallback returns a
trained label. Rule confidence is not treated as a calibrated probability.

## Calibration metrics

Expected calibration error uses ten equal-width confidence bins. Within each
bin it compares mean confidence with empirical accuracy and weights the gap by
the bin's sample fraction. The multiclass Brier score is the mean, across rows,
of the summed squared difference between the predicted probability vector and
the one-hot true label. Lower values are better for both measures.

## Robustness conditions

The frozen text is transformed without changing its intended label under five
controlled conditions:

- case and punctuation removal;
- repeated whitespace;
- common Romanized Hinglish spelling variants;
- digit masking; and
- OCR-style substitutions such as `o`/`0`, `l`/`1`, and `s`/`5`.

These are deterministic simulations. They do not replace evaluation on
naturally collected noisy complaints or screenshots.

## Statistical comparison

Hypothesis H1 pre-registers character TF-IDF as model A and word TF-IDF as
model B before reading their frozen-test scores. The paired bootstrap resamples
the same test-row indices for both candidates, preserving the paired nature of
their predictions. It uses seed 42 and 2,000 resamples to estimate the Macro-F1
difference and its percentile 95% confidence interval. A positive interval is
evidence only for this frozen split. With eight rows, the interval cannot
establish real-world superiority.

## Reproducibility and interpretation rules

- Generated JSON and CSV omit wall-clock values.
- Compact CSV and audit evidence is committed; verbose diagnostics are
  regenerated twice and byte-compared in CI.
- CI regenerates all research artifacts and compares them byte-for-byte.
- Published accuracy is always accompanied by its original task and dataset.
- A larger value from a different task is not a shared-leaderboard win.
- “Better classifier” requires a same-test improvement with uncertainty.
- “Better system” can instead mean a documented trade-off across classification,
  evidence extraction, OCR, explainability, privacy, and deployability.
