# FraudLens Bharat - Phase 1

FraudLens Bharat is a pure-software cyber-fraud triage prototype for Indian users. Phase 1 focuses on a reliable baseline system that analyzes pasted scam messages, classifies the fraud type, extracts useful evidence, scores risk, and generates a complaint-ready summary.

The project is designed for my capstone project submission. It includes implementation code, dataset scaffolding, testing evidence, documentation, references, and demo cases aligned with the provided capstone format and rubric.

## Current Phase 1 Evidence

- Dataset: 64 synthetic, manually reviewed bootstrap examples across 8 fraud classes; no `legitimate` rows are present
- Selected model: calibrated raw-normalized TF-IDF + Logistic Regression, trained only on the frozen 48-row train split and thresholded on the 8-row validation split
- Frozen 8-row synthetic test: 0.5000 overall accuracy and 0.5000 raw macro-F1; 87.5% coverage, 12.5% abstention, and 57.14% accepted accuracy
- The Phase 2 target is not met: the bootstrap is below 200 examples per label and lacks the `legitimate` label
- Rule fallback: used only if calibrated artifacts are unavailable or corrupt, and abstains on weak generic keyword matches
- Interfaces: FastAPI backend and Streamlit dashboard
- Evidence outputs: calibrated artifact metadata, metrics JSON, demo cases, screenshots, and pitch deck

These synthetic bootstrap results are not a production accuracy claim.

## Phase 1 Scope

- Hinglish/Hindi/English scam text analysis
- Eight fraud classes: KYC scam, digital arrest, fake job, investment scam, loan scam, courier scam, UPI refund scam, OTP/phishing scam
- Calibrated TF-IDF + Logistic Regression classifier with an abstention threshold
- Rule-based fallback only when model artifacts cannot be loaded
- Entity extraction for phone numbers, UPI IDs, URLs, emails, money amounts, OTP-like codes, urgency phrases, and threat phrases
- URL and identifier risk scoring
- FastAPI backend
- Streamlit dashboard
- Optional SQLite case history. API and compatibility callers default to off unless `FRAUDLENS_STORE_CASES=true` is configured; the dashboard always requires explicit consent.
- Unit/API tests
- Metrics and demo case outputs

OCR, transformer fine-tuning, graph analytics, and screenshot analysis are intentionally reserved for Phase 2.

## Setup

```bash
cd "/Users/gautammanch/capstone-project(phase-1)"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## Train Baseline Model

```bash
python -m fraudlens.model_training
```

This creates:

- `models/baseline_classifier.joblib`
- `models/vectorizer.joblib`
- `models/label_encoder.joblib`
- `models/metrics.json`
- `models/model_metadata.json`

## Run API

```bash
uvicorn fraudlens.api:app --reload
```

Open the interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

`POST /analyze` accepts an optional `store_case` boolean. Omitting it uses the
safe API runtime default (`false` unless `FRAUDLENS_STORE_CASES=true`). The
compatibility helper follows the same setting. Responses include prediction
provenance, abstention status, and whether the case was actually stored.

When storage is enabled, the full analysis record is retained only for the
configured `FRAUDLENS_RETENTION_DAYS` period. Case-to-case entity links use
secret-keyed opaque IDs and display masks; raw phone numbers, UPI IDs, email
addresses, and URLs are never written to the entity-link table. During
migration, legacy records with a valid creation timestamp receive the configured
retention deadline and expired records are purged. Rows with malformed retention
timestamps are deleted rather than retaining raw text indefinitely.

## Run Dashboard

```bash
streamlit run src/fraudlens/dashboard.py
```

The dashboard's “Store this analysis locally” checkbox is always off by default,
even when the API/compatibility storage setting is enabled.

## Run Tests

```bash
pytest
```

## Demo Cases

Four reproducible demo case outputs are stored in `outputs/demo_cases/` after running:

```bash
python -m fraudlens.generate_demo_cases
```

## Documentation Map

- `docs/phase1_report.md`: main capstone report
- `docs/literature_review.md`: research context and source-backed literature review
- `docs/comparative_analysis.md`: initial-state, rule-only, hybrid, and external-model comparison
- `docs/evaluation_plan.md`: metrics and accuracy-maintenance plan
- `docs/model_card.md`: Phase 1 model/data card
- `docs/references.md`: IEEE-style source list
- `docs/test_cases.md`: Phase 1 test case inventory
- `docs/user_manual.md`: dashboard usage guide
- `docs/installation_guide.md`: setup and run instructions

## Ethical Guardrails

- No real victim PII is required.
- The seed dataset is synthetic and educational.
- The prototype does not submit complaints automatically.
- The generated summary is only an assistive draft for manual reporting.
