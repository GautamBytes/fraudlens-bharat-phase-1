# FraudLens Bharat

FraudLens Bharat is a pure-software cyber-fraud triage prototype for Indian users. It analyzes pasted scam messages or screenshots, classifies the fraud type, extracts useful evidence, scores risk, and generates a complaint-ready summary.

The project is designed for my capstone project submission. It includes implementation code, dataset scaffolding, testing evidence, documentation, references, and demo cases aligned with the provided capstone format and rubric.

## Current Phase 2 Evaluation Evidence

- Dataset: 64 synthetic, manually reviewed bootstrap examples across 8 fraud classes; no `legitimate` rows are present
- Selected runtime candidate: calibrated raw-normalized TF-IDF + Logistic Regression, fit and calibrated only on the frozen 48-row train split and thresholded on the 8-row validation split
- Frozen 8-row synthetic test evidence is committed in `outputs/phase2/evaluation.json` and `outputs/phase2/summary.txt`; it compares rule-only, raw TF-IDF, marker TF-IDF ablation, and calibrated TF-IDF without using the test split for fitting or threshold selection
- Rule-only evidence calls the canonical runtime fallback for every frozen row. Its runtime acceptance is `label != unknown`; it does not receive an evaluator-tuned threshold or calibration score.
- The Phase 2 target is not met: the bootstrap is below 200 examples per label and lacks the `legitimate` label
- Rule fallback: used only if calibrated artifacts are unavailable or corrupt, and abstains on weak generic keyword matches
- Interfaces: FastAPI backend and Streamlit dashboard
- Evidence outputs: calibrated artifact metadata, metrics JSON, demo cases, screenshots, and pitch deck

These synthetic bootstrap results are not a production accuracy claim.

## Current Scope

- Hinglish/Hindi/English scam text analysis
- Eight fraud classes: KYC scam, digital arrest, fake job, investment scam, loan scam, courier scam, UPI refund scam, OTP/phishing scam
- Calibrated TF-IDF + Logistic Regression classifier with an abstention threshold
- Rule-based fallback only when model artifacts cannot be loaded
- Entity extraction for phone numbers, UPI IDs, URLs, emails, money amounts, OTP-like codes, urgency phrases, and threat phrases
- URL and identifier risk scoring
- FastAPI backend
- Streamlit dashboard with text and screenshot input
- Local Tesseract OCR for English and Hindi screenshot text
- Optional SQLite case history. API and compatibility callers default to off unless `FRAUDLENS_STORE_CASES=true` is configured; the dashboard always requires explicit consent.
- Privacy-safe, observational entity relationship graph for repeated evidence in stored cases
- Unit/API tests
- Metrics and demo case outputs

OCR and basic graph analytics are now present. Transformer fine-tuning and GNN
models remain outside the current scope.

## Setup

FraudLens Bharat requires Python 3.10 or later.

### Runtime installation

Install Tesseract and its English and Hindi language data before using screenshot
analysis.

On macOS with Homebrew:

```bash
brew install tesseract tesseract-lang
```

On Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
```

Then install the Python runtime requirements to run the API, dashboard, or
training command:

```bash
cd "/Users/gautammanch/capstone-project(phase-1)"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
```

### Contributor and test installation

Contributors should install the development requirements, which include the
runtime dependencies and `pytest`:

```bash
pip install -r requirements-dev.txt
pip install -e . --no-deps
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

## Inspect Stored Entity Relationships

`GET /graph` is an investigative view of **explicitly stored, unexpired cases**
only. It links repeated phone numbers, UPI IDs, email addresses, and URLs across
those cases. Analyses that were not stored, and cases removed by retention, are
not graph inputs.

The endpoint defaults to `minimum_case_count=2` and `case_limit=100`.
minimum_case_count must be between 2 and 20, and case_limit must be between 1
and 100. The graph uses a fixed internal max_edges=1000 bound; it is not an API
query parameter. For example:

```bash
curl "http://127.0.0.1:8000/graph?minimum_case_count=2&case_limit=100"
```

API entity nodes expose opaque HMAC-backed identifiers and masked labels. Graph
output does not include raw text or raw entity values. An empty result means
there are no qualifying stored cases for the selected threshold. A `truncated`
result means the safe case or link display limit was reached; narrow the
investigation before drawing conclusions.

Deleting a case, clearing case history, or retention expiry removes its graph
links. The graph is observational: it does not change a case's risk score or
fraud classification, does not perform fraud-network detection, and is not a
production fraud-network claim or a GNN.

`POST /analyze-image` accepts a raw PNG or JPEG body. For example:

```bash
curl -X POST "http://127.0.0.1:8000/analyze-image?store_case=false" \
  -H "Content-Type: image/png" \
  --data-binary @screenshot.png
```

Screenshot input supports PNG and JPEG files up to 5 MiB, with dimensions no
larger than 4096 x 4096 and no more than 16,000,000 pixels. Tesseract reads
English and Hindi (`eng+hin`). Images are never retained. OCR text is stored only
when you explicitly enable local case storage; the same configured retention
period used for pasted text then applies.

## Run Dashboard

```bash
streamlit run src/fraudlens/dashboard.py
```

Use the **Screenshot** tab to choose a PNG or JPEG and click **Analyze
Screenshot**. The dashboard's “Store this analysis locally” checkbox is always
off by default, even when the API/compatibility storage setting is enabled.

The **Entity Graph** tab does not run the graph query until explicit Refresh
Graph is selected after choosing a threshold. The page can still read **Recent
Analysis History** separately. The dashboard shows masked labels and hides
opaque identifiers; it presents the same privacy-safe, bounded evidence as
`GET /graph`.

## Run Tests

```bash
pytest
```

## Reproduce Phase 2 Evaluation

```bash
python -m fraudlens.evaluation \
  --dataset data/samples/phase2_dataset.csv \
  --output outputs/phase2
```

This writes deterministic `evaluation.json` and a readable `summary.txt`.
The report intentionally omits wall-clock timings, which are not stable enough
for byte-for-byte reproducible evidence. It records that the 64-row synthetic
bootstrap is missing `legitimate` and does not meet the 200-rows-per-label target.

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
