# FraudLens Bharat - Phase 1

FraudLens Bharat is a pure-software cyber-fraud triage prototype for Indian users. Phase 1 focuses on a reliable baseline system that analyzes pasted scam messages, classifies the fraud type, extracts useful evidence, scores risk, and generates a complaint-ready summary.

The project is designed for my capstone project submission. It includes implementation code, dataset scaffolding, testing evidence, documentation, references, and demo cases aligned with the provided capstone format and rubric.

## Current Phase 1 Evidence

- Seed dataset: 64 synthetic, manually reviewed examples across 8 fraud classes
- Rule-only fallback: 0.8125 accuracy and 0.7833 macro-F1 on the current 16-row synthetic test split
- Hybrid baseline: 1.0000 accuracy and 1.0000 macro-F1 on the same synthetic test split
- Interfaces: FastAPI backend and Streamlit dashboard
- Evidence outputs: metrics JSON, classification report, confusion matrix, demo cases, screenshots, and pitch deck

The 1.0000 score is an internal synthetic benchmark, not a production accuracy claim.

## Phase 1 Scope

- Hinglish/Hindi/English scam text analysis
- Eight fraud classes: KYC scam, digital arrest, fake job, investment scam, loan scam, courier scam, UPI refund scam, OTP/phishing scam
- TF-IDF + Logistic Regression baseline classifier
- Rule-based fallback classifier for robust demos
- Entity extraction for phone numbers, UPI IDs, URLs, emails, money amounts, OTP-like codes, urgency phrases, and threat phrases
- URL and identifier risk scoring
- FastAPI backend
- Streamlit dashboard
- SQLite case history
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
- `outputs/metrics/classification_report.txt`
- `outputs/metrics/confusion_matrix.png`

## Run API

```bash
uvicorn fraudlens.api:app --reload
```

Open the interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Run Dashboard

```bash
streamlit run src/fraudlens/dashboard.py
```

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
