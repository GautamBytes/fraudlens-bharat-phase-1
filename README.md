# FraudLens Bharat

FraudLens Bharat is a pure-software cyber-fraud triage prototype for Indian users. It analyzes pasted scam messages or screenshots, classifies the fraud type, extracts useful evidence, scores risk, and generates a complaint-ready summary.

The project is designed for my capstone project submission. It includes implementation code, dataset scaffolding, testing evidence, documentation, references, and demo cases aligned with the provided capstone format and rubric.

## Release 1.0

Release 1.0 is the final Phase 2 software release of the capstone prototype. It
aligns package/API identity, adds dependency-aware readiness, emits
privacy-safe structured request logs, and supplies a pinned, non-root container
for the API and website. This release designation means the planned software
scope is integrated and release-tested; it does not turn the synthetic
evaluation into a production accuracy claim.

[Open the hosted professor website](https://fraudlens-bharat.vercel.app) for
the fastest no-installation evaluation path.

For a local production-style launch of the modern professor web experience:

```bash
cp .env.example .env
# Put a unique secrets.token_urlsafe(48) value in FRAUDLENS_HMAC_SECRET.
docker compose up --build --detach
```

The API is available at `http://127.0.0.1:8000` and the website at
`http://127.0.0.1:3000`. `GET /health` is process liveness; `GET /ready` also
checks the initialized case store. Both report version `1.0.0`. See
`docs/professor_testing_guide.md` for the recommended hosted and local test
sequence, see `docs/deployment_guide.md` before changing exposure, and use
`docs/release_checklist.md` for the release gate.

## Current Phase 2 Evaluation Evidence

- Dataset: 64 synthetic, manually reviewed bootstrap examples across 8 fraud classes; no `legitimate` rows are present
- Selected runtime candidate: calibrated raw-normalized TF-IDF + Logistic Regression, fit and calibrated only on the frozen 48-row train split and thresholded on the 8-row validation split
- Frozen 8-row synthetic test evidence is committed in `outputs/phase2/evaluation.json` and `outputs/phase2/summary.txt`; it compares rule-only, raw TF-IDF, marker TF-IDF ablation, and calibrated TF-IDF without using the test split for fitting or threshold selection
- Rule-only evidence calls the canonical runtime fallback for every frozen row. Its runtime acceptance is `label != unknown`; it does not receive an evaluator-tuned threshold or calibration score.
- The Phase 2 target is not met: the bootstrap is below 200 examples per label and lacks the `legitimate` label
- Rule fallback: used only if calibrated artifacts are unavailable or corrupt, and abstains on weak generic keyword matches
- Interfaces: modern Next.js professor website and FastAPI backend
- Evidence outputs: calibrated artifact metadata, metrics JSON, demo cases, screenshots, and pitch deck

These synthetic bootstrap results are not a production accuracy claim.

### Hybrid evaluation evidence

The final research package now keeps four evidence tracks separate:

- internal eight-class synthetic evaluation;
- external binary validation on all 5,574 UCI SMS Spam Collection records,
  with normalized duplicate groups kept within one split;
- deployed-runtime abstention and escalation behavior on 748 held-out ham
  messages; and
- controlled entity, URL, graph, OCR and complaint-template benchmarks.

The calibrated character candidate reached 98.60% accuracy, 0.9682 Macro-F1,
0.9273 spam recall and 0.0071 ECE on the 858-message external binary test. The
paired character-vs-word Macro-F1 interval crosses zero, so it is not presented
as a statistically decisive win. The OCR benchmark used 24 real Tesseract runs
and recorded 0% failures with 91.67% downstream label agreement. See
`outputs/evaluation/` and `docs/phase2_research_report.md`. Only aggregate
evidence is tracked; raw UCI messages, row predictions and externally trained
artifacts are not committed. These results are not production accuracy.

## Final Capstone Package

The final Phase 1 + Phase 2 meeting package is source-backed and uses the
provided 10-slide college template:

- `docs/final_capstone_report.md`: consolidated implementation and research report
- `docs/presentation/fraudlens-bharat-final-capstone.pptx`: final 15-minute deck
- `docs/presentation/demo_video_runbook.md`: live-demo and recording sequence
- `outputs/presentation/`: current architecture and evaluation figures
- `outputs/screenshots/final_*.png`: synthetic final application evidence

The deck keeps the deployed calibrated runtime result separate from the
stronger research-only character TF-IDF candidate. It states the 64-row
synthetic, fraud-only dataset limitation and makes no production-accuracy
claim.

## Research Benchmark

The capstone now includes a same-split academic benchmark of canonical rules,
word TF-IDF, character TF-IDF, word-character TF-IDF, and a calibrated hybrid.
On the eight-row frozen synthetic test, character TF-IDF and the word-character
hybrid each reach 0.7500 accuracy and 0.6667 macro-F1. This is promising
internal evidence, not production accuracy: the dataset remains 64 synthetic
fraud-only rows and has no legitimate examples. The benchmark does not replace
the release's selected calibrated runtime artifact.

Read `docs/phase2_research_report.md` for the literature comparison, metric
rationale, error analysis, robustness study, statistical interpretation, and
threats to validity. Committed compact evidence is in
`outputs/research/classification_summary.csv`,
`outputs/research/ablation_summary.csv`, and the dataset audit in the same
directory. The full diagnostic JSON is generated locally by the reproduction
commands and compared run-to-run in CI, but ignored by Git to keep reviews
concise.

## Current Scope

- Hinglish/Hindi/English scam text analysis
- Eight fraud classes: KYC scam, digital arrest, fake job, investment scam, loan scam, courier scam, UPI refund scam, OTP/phishing scam
- Calibrated TF-IDF + Logistic Regression classifier with an abstention threshold
- Rule-based fallback only when model artifacts cannot be loaded
- Entity extraction for phone numbers, UPI IDs, URLs, emails, money amounts, OTP-like codes, urgency phrases, and threat phrases
- URL and identifier risk scoring
- FastAPI backend
- Modern responsive professor website with text and screenshot analysis, relationship evidence, research comparison, and an in-app run guide
- Local Tesseract OCR for English and Hindi screenshot text
- Optional SQLite case history. API requests default to off unless `FRAUDLENS_STORE_CASES=true` is configured; the website requires explicit consent.
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

Then install the Python runtime requirements to run the API or training command:

```bash
cd /path/to/fraudlens-bharat
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
safe API runtime default (`false` unless `FRAUDLENS_STORE_CASES=true`). Responses
include prediction provenance, abstention status, and whether the case was
actually stored.

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

## Use the Website

Open the [hosted FraudLens Bharat website](https://fraudlens-bharat.vercel.app)
for the professor path, or start the complete local stack with
`docker compose up --build --detach` and open
`http://127.0.0.1:3000`. Use `/analyze` for message or screenshot analysis and
`/relationships` to review relationship evidence. The message tab corresponds
to `POST /analyze`; the screenshot tab corresponds to `POST /analyze-image`.

The relationship view includes only explicitly stored, unexpired cases. It
does not run the graph query until explicit Build synthetic link or Refresh.
The website shows masked labels and hides opaque identifiers; it
presents the same privacy-safe, bounded evidence as `GET /graph`.

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

To reproduce the external binary benchmark, download the official UCI archive
outside the repository and run:

```bash
python -m fraudlens.external_evaluation \
  --archive /path/to/sms-spam-collection.zip \
  --output outputs/evaluation \
  --bootstrap-samples 2000
```

The command refuses an archive whose SHA-256 or 5,574-row contract differs from
the pinned source. Run `python -m fraudlens.subsystem_evaluation --output
outputs/evaluation` in the pinned Docker image for canonical Tesseract evidence.

## Demo Cases

Four reproducible demo case outputs are stored in `outputs/demo_cases/` after running:

```bash
python -m fraudlens.generate_demo_cases
```

## Documentation Map

- `docs/final_capstone_report.md`: consolidated final Phase 1 + Phase 2 report
- `docs/phase2_research_report.md`: detailed benchmark, literature comparison, and validity analysis
- `docs/research_methodology.md`: frozen-split protocol and metric rationale
- `docs/presentation/fraudlens-bharat-final-capstone.pptx`: final template-based presentation
- `docs/presentation/demo_video_runbook.md`: recording and failure-safe demo plan
- `docs/phase1_report.md`: historical Phase 1 progress report
- `docs/literature_review.md`: research context and source-backed literature review
- `docs/comparative_analysis.md`: initial-state, rule-only, hybrid, and external-model comparison
- `docs/evaluation_plan.md`: metrics and accuracy-maintenance plan
- `docs/model_card.md`: Phase 1 model/data card
- `docs/references.md`: IEEE-style source list
- `docs/test_cases.md`: Phase 1 test case inventory
- `docs/user_manual.md`: website usage guide
- `docs/installation_guide.md`: setup and run instructions
- `docs/deployment_guide.md`: hardened Docker deployment, backup, monitoring, and rollback
- `docs/release_checklist.md`: final pre-release and post-release verification gate

## Ethical Guardrails

- No real victim PII is required.
- The seed dataset is synthetic and educational.
- The prototype does not submit complaints automatically.
- The generated summary is only an assistive draft for manual reporting.
