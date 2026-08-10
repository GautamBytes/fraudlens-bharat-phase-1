# FraudLens Bharat Final Capstone Presentation Script

Target duration: 15 minutes

Speaking target: 14 minutes, leaving about 60 seconds for transition or one
question.

## Slide 1 - FraudLens Bharat (0:00-0:45)

Good morning. I am Gautam Manchandani, student ID 2023EBCS209. My capstone is
FraudLens Bharat, a local and explainable cyber-fraud triage prototype for
Indian messages and screenshots.

This is the final Phase 1 + Phase 2 system. A user can paste suspicious text or
upload a bounded screenshot. The project classifies the scam type, extracts
evidence such as phone numbers, UPI IDs and URLs, explains its risk reasons, and
creates a complaint draft. It can also show repeated masked entities across
cases that the user chose to retain.

I will cover the problem, research comparison, architecture, live workflow,
results, limitations, and the specific evidence needed before this could move
beyond a college prototype.

## Slide 2 - Problem Statement (0:45-1:45)

Cyber-fraud evidence reaches a victim in an inconvenient form. It may be an
SMS, WhatsApp message, email, URL, payment identifier, or screenshot. The text
can mix English and Hindi, use Hindi in Roman script, contain spelling changes,
and create urgency through threats such as account blocking or arrest.

The reporting gap has three parts. First, the victim has unstructured evidence,
not a formal complaint. Second, a classifier label alone does not preserve the
phone, UPI ID, amount, URL, or threat that an investigator needs. Third, a
system can create more harm if it hides uncertainty or stores sensitive text
without consent.

FraudLens addresses this as assistive triage. It structures evidence and
explains the result. Human review required: the system does not decide whether
a crime occurred and never files a complaint automatically.

## Slide 3 - Objectives & Scope (1:45-2:50)

The project has five measurable objectives. It classifies eight common scam
types. It extracts complaint evidence. It returns visible risk reasons and can
abstain when confidence is low. It supports both pasted text and local OCR. It
also makes storage optional, applies retention, and masks repeated identifiers
in the graph view.

Phase 1 built the foundation: taxonomy, preprocessing, TF-IDF training,
entities, URL checks, risk scoring, FastAPI, Streamlit, SQLite, tests, and
documentation.

Phase 2 completed screenshot OCR, calibrated inference with abstention,
privacy-safe entity relationships, reproducible model comparisons, container
hardening, and final evidence.

The boundaries matter. This is a loopback local prototype. It does not fine-tune
a transformer, train a GNN, block transactions, expose a public service, or
claim production accuracy.

## Slide 4 - Existing System / Literature Review (2:50-4:15)

I compared solution families rather than placing unrelated percentages on one
leaderboard.

Rules are cheap and transparent, but brittle. On my frozen split, rules reach
25 percent accuracy and Macro-F1 at only 25 percent coverage. Word TF-IDF is a
strong lightweight baseline, but it treats spelling and Romanized variants as
different words. Character TF-IDF shares substrings across those variants and
is the best local research candidate.

For external context, Rani and colleagues report 74.41 percent accuracy and
71.49 percent F1 with HingRoBERTa on an I4C complaint task. A neural phishing
URL study reports about 97 percent validation accuracy. Graph-fraud studies use
account or transaction networks and do not have one universal score.

Those numbers are not directly comparable to FraudLens. They use different
inputs, labels, and datasets. The defensible contribution here is the integrated
workflow: classification, OCR, evidence, explanation, complaint drafting,
consent, retention, masked relationships, and reproducible local deployment.

## Slide 5 - Proposed System Architecture (4:15-5:40)

Both input routes converge on one analysis service. Text enters directly.
Screenshots first pass format, size, dimension, frame, and decompression checks;
Tesseract reads English and Hindi locally, and image bytes are discarded.

The service normalizes text and runs four evidence paths: the calibrated
classifier, entity extraction, URL checks, and rule signals. It applies the
confidence threshold, combines visible signals into low, medium, or high risk,
and produces a complaint draft.

FastAPI and Streamlit display the same result. Storage stays off unless the user
chooses it. Retained cases expire. The graph reads only unexpired consented
cases and uses HMAC identifiers plus masked labels, so raw phone numbers, UPI
IDs, email addresses, and URLs do not enter the relationship table.

The release verifies model hashes before deserialization and runs as a
non-root, read-only local container. The graph is an observational link view,
not a GNN and not a fraud-network detector.

## Slide 6 - Tools & Technologies (5:40-6:30)

The implementation uses Python 3.10 or later. Scikit-learn provides TF-IDF,
Logistic Regression, and probability calibration. FastAPI exposes the service,
while Streamlit provides the demo interface. SQLite stores consented local case
history. Tesseract performs offline English and Hindi OCR.

Pydantic validates service boundaries, Pillow checks image policy, and pytest
drives 379 automated tests. Joblib stores the fitted artifacts, but the runtime
verifies their hashes before loading. Docker Compose supplies a loopback-only,
non-root, read-only deployment. GitHub Actions tests Python 3.10, canonical
3.11.15, Python 3.12, reproducible evidence, and the container path.

No paid API or cloud model is required for the demo.

## Slide 7 - Implementation / Demo (6:30-9:30)

I will show three flows. I have synthetic inputs prepared so no real victim data
appears in the recording.

First, in the Text Analysis tab, I select the Fake KYC SMS demo and run it. The
result shows the advertised scam category, confidence, medium or high risk,
extracted entities, visible reasons, and a complaint-ready draft. Storage is
off, which proves the safe default.

Second, in Screenshot Analysis, I upload the prepared PNG. The system validates
the file, runs local English and Hindi OCR, shows the extracted text, and sends
that text through the same analysis service. The result states that source image
bytes were not retained.

Third, I enable consent for two synthetic messages that share the host
`fraud-demo.example`. In Entity Graph I click Refresh Graph. The system shows two
incidents linked through a masked shared URL host. It does not display a raw
victim identifier and does not alter either prediction.

If the live process is unavailable, the committed final screenshots show these
same flows. The API readiness and Swagger screenshots provide a second fallback.

## Slide 8 - Results & Analysis (9:30-11:30)

The dataset contains 64 synthetic fraud-only messages: 48 train, 8 validation,
and 8 frozen test. There is no legitimate class. One test row represents each
fraud category.

On that fixed split, word TF-IDF reaches 37.5 percent accuracy and 33.33 percent
Macro-F1. Character TF-IDF and the word-character hybrid each reach 75.0%
accuracy and 66.67% Macro-F1. Because the hybrid gives the same decisions with
a larger fitted payload, character-only is the preferred research candidate.

The pre-registered character-versus-word Macro-F1 difference is plus 0.3333.
Its 2,000-sample paired-bootstrap interval is 0.0498 to 0.4084. This supports a
character-feature hypothesis only for the frozen split.

The deployed calibrated model is different: it has 50.0% runtime accuracy,
50.0 percent Macro-F1, and 87.5% coverage. Calibration improves probability
quality but reduces classification accuracy with only 48 training rows.

I compare accuracy, Macro-F1, balanced accuracy, MCC, per-class errors,
coverage, calibration, fitted bytes, robustness, and confusion matrices. OCR,
entity, URL, graph, complaint quality, latency, and memory need their own
labelled benchmarks.

## Slide 9 - Challenges & Limitations (11:30-12:30)

The main challenge was preventing a complete software demo from looking like a
validated production detector. The dataset is synthetic and small, has no
benign examples, and gives each class one test row. A single error moves
accuracy by 12.5 points. The character model still misses digital arrest and
OTP phishing on the frozen test.

There is no labelled screenshot corpus for OCR character or word error rate, no
entity precision and recall dataset, no URL PR-AUC benchmark, no graph edge
ground truth, no usability study, and no standardized latency experiment.

The controls respond to those limits: confidence can abstain, reasons remain
visible, storage requires consent, screenshots are discarded, graph labels are
masked, retention deletes old data, and no request body enters logs. The deck
makes no production-accuracy claim.

## Slide 10 - Conclusion & Future Work (12:30-14:00)

FraudLens Bharat meets the planned Phase 1 + Phase 2 software scope. It combines
text and screenshot triage, evidence extraction, URL signals, uncertainty,
complaint drafting, privacy controls, repeated-entity visualization, and a
reproducible local release. The codebase has 379 automated tests and green
multi-version and container checks.

The research result identifies character TF-IDF as the most promising
lightweight representation on the current split. It does not establish
real-world superiority.

My next research target is an authorized dataset with at least 200 reviewed
examples per fraud label plus legitimate controls and an external grouped test.
On that data I would compare character TF-IDF and a Hinglish transformer under
the same protocol. I would also build labelled benchmarks for OCR, entities,
URLs, graph links, complaint quality, latency, memory, and user review.

In one sentence: FraudLens Bharat turns messy scam evidence into a structured,
explainable, privacy-aware draft while keeping the final decision with a human.

Thank you. I am ready for questions.

## Timed rehearsal checklist

| Time | Checkpoint | Maximum drift |
|---|---|---:|
| 0:45 | Leave title | 10 seconds |
| 2:50 | Begin literature comparison | 15 seconds |
| 6:30 | Begin live demo | 20 seconds |
| 9:30 | Begin results | 20 seconds |
| 12:30 | Begin conclusion | 20 seconds |
| 14:00 | Finish prepared talk | 15 seconds |
| 15:00 | End transition or first question | hard stop |

Rehearse once with the live application and once using screenshots only. Do not
improvise new accuracy claims. If asked whether 75 percent beats the published
74.41 percent result, answer that the datasets and taxonomies differ, so the
values cannot support that conclusion.
