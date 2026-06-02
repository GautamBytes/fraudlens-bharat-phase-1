# FraudLens Bharat - Phase 1

FraudLens Bharat is a pure-software cyber-fraud triage prototype for Indian users. Phase 1 focuses on a reliable baseline system that analyzes pasted scam messages, classifies the fraud type, extracts useful evidence, scores risk, and generates a complaint-ready summary.

The project is designed for my capstone project submission. It includes implementation code, dataset scaffolding, testing evidence, documentation, references, and demo cases aligned with the provided capstone format and rubric.

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

## Ethical Guardrails

- No real victim PII is required.
- The seed dataset is synthetic and educational.
- The prototype does not submit complaints automatically.
- The generated summary is only an assistive draft for manual reporting.

