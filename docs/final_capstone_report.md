# FraudLens Bharat Final Capstone Report

**Student:** Gautam Manchandani

**Student ID:** 2023EBCS209

**Programme:** BSc Computer Science, BITS Pilani Digital

**Supervisor:** Dr. Ashok Yemineni

**Release:** 1.0.0, Phase 1 + Phase 2

## Executive Summary

FraudLens Bharat is a local cyber-fraud triage prototype for suspicious Indian
messages and screenshots. A user submits English, Hindi, or Romanized Hinglish
evidence. The system classifies one of eight scam categories, extracts useful
identifiers, checks URLs, explains a risk score, and creates a complaint draft.
It can read bounded PNG/JPEG screenshots through local Tesseract OCR and show
repeated masked entities across cases that the user chose to retain.

Phase 1 established the text-analysis pipeline, FastAPI, a retired Phase 1
demonstration interface, SQLite storage, tests, and documentation. Phase 2
added calibrated inference with abstention, screenshot OCR, privacy-safe entity
relationships, reproducible model research, release hardening, and final
presentation evidence. The completed codebase has 369 automated tests and runs
through the Next.js website and FastAPI, including a hardened local container
path.

The best research candidate, character TF-IDF, reaches 75.0% accuracy and
66.67% Macro-F1 on the frozen test. It doubles the word-only Macro-F1 and
matches the hybrid's decisions with a 20.3% smaller estimated fitted payload.
The deployed runtime instead prioritizes calibrated confidence and abstention:
it reaches 50.0% accuracy, 50.0% Macro-F1, 87.5% coverage, and 12.5%
abstention. These data-backed results make FraudLens a strong, inspectable
student system while preserving an important boundary: the 64 messages are
synthetic, there is no legitimate class, and the test has one message per scam
class.

## Problem Statement

Indian cyber-fraud evidence often arrives as an SMS, WhatsApp message, email,
payment identifier, URL, or screenshot. A victim may receive English and Hindi
in the same sentence, Hindi written in Roman script, deliberate spelling
changes, threats, urgency, and instructions to share an OTP or transfer money.
That evidence does not arrive as a structured complaint.

Classifier-only systems leave several tasks to the user. The user must identify
the scam type, copy important identifiers, decide whether a link looks unsafe,
explain the urgency or threat, and rewrite the message as a report. FraudLens
Bharat addresses that workflow as an assistive triage tool. It does not decide
whether a crime occurred and does not submit a government complaint.

## Objectives And Scope

The project has five objectives:

1. classify eight common Indian scam-message categories;
2. preserve useful evidence such as phones, UPI IDs, emails, URLs, amounts, and
   OTP-like codes;
3. expose risk reasons and uncertainty instead of returning a label alone;
4. accept pasted text and bounded screenshot input through one analysis path;
5. retain data only with consent and show repeated entities without exposing
   their raw values in graph storage or output.

The release covers a local educational prototype. It excludes automatic NCRP
filing, transaction blocking, public internet deployment, transformer
fine-tuning, GNN fraud detection, and any legal conclusion.

## Phase 1 Foundation

Phase 1 produced the first complete vertical slice:

- an eight-label taxonomy and synthetic no-PII dataset;
- deterministic preprocessing for mixed-language scam text;
- TF-IDF and Logistic Regression training and inference;
- extraction of URLs, phones, UPI IDs, email addresses, money amounts,
  OTP-like codes, urgency phrases, and threats;
- auditable URL and identifier rules;
- explainable low, medium, or high risk scoring;
- a complaint-draft template;
- FastAPI endpoints, the now-retired Phase 1 demonstration interface, SQLite
  history, tests, and installation documentation.

The Phase 1 API and demonstration interface used the same analysis service.
The supported final Next.js website continues to use that shared FastAPI-backed
pipeline for its user-facing workflow.

## Phase 2 Completion

Phase 2 completed four areas.

### Screenshot OCR

The screenshot workflow accepts PNG and JPEG images up to 5 MiB, at most
4096 x 4096 pixels and 16 million total pixels. It checks the encoded format,
dimensions, frames, decompression risk, and timeout before local Tesseract OCR
with `eng+hin`. The service analyzes the extracted text and discards image
bytes. OCR text enters SQLite only when the user selects storage consent.

### Selective and reproducible inference

The deployed model uses calibrated TF-IDF probabilities and a validation-set
threshold. Predictions below the threshold become `unknown`. Model files carry
hashes and training provenance; inference reads and verifies immutable bytes
before deserialization. CI retrains the canonical artifacts and compares every
release file byte-for-byte.

### Privacy-safe entity relationships

The graph view reads unexpired, consented cases. It links repeated phones, UPI
IDs, emails, and URL hosts through secret-keyed HMAC identifiers and masked
display labels. It never stores a raw entity in the relationship table. The
graph is observational: it does not alter classification or risk, and it is not
a GNN or fraud-network detector.

### Release hardening

The final release uses pinned dependency locks, a non-root read-only container,
least-privilege GitHub Actions, privacy-safe logs, readiness checks, retention
purging, and deterministic evaluation outputs. Runtime and development lock
audits report no known vulnerabilities at the PR 1 release gate.

## System Architecture

The text and screenshot routes converge on one service:

1. **Input boundary:** validate text or image policy; OCR stays local.
2. **Preprocessing:** normalize text while preserving evidence tokens.
3. **Parallel evidence:** run calibrated classification, entity extraction,
   URL checks, and rule signals.
4. **Decision:** apply abstention and combine visible signals into risk.
5. **Output:** return the label, confidence, provenance, entities, reasons, and
   complaint draft through FastAPI and the Next.js website.
6. **Optional retention:** store only with explicit consent and remove expired
   cases and links.
7. **Graph read:** aggregate repeated masked entities across retained cases.

The committed architecture diagram is
`outputs/presentation/final_system_architecture.png`.

## Research Questions

- **RQ1:** Do character n-grams improve frozen-test Macro-F1 over word-only
  TF-IDF for the current Hinglish/English messages?
- **RQ2:** Does combining word and character features improve the character
  candidate enough to justify the larger fitted payload?
- **RQ3:** Does sigmoid calibration improve probability quality without
  reducing classification quality?
- **RQ4:** Do character features remain more stable under bounded language and
  OCR-style perturbations?
- **RQ5:** Which system-level properties make the prototype useful when
  external accuracy superiority cannot be claimed?

The protocol fixes train, validation, and test rows before fitting. Train fits
vocabularies and coefficients, validation selects abstention thresholds, and
test measures the final candidates once. Seed 42 controls fitted models and the
2,000-sample paired bootstrap.

## Dataset And Ethics

The CSV has 64 synthetic messages: 48 train, 8 validation, and 8 test. It
contains eight fraud labels, eight rows per label, 36 English rows, and 28
Hinglish rows. No row contains real victim PII. No legitimate example exists.

One test row per class means one error changes accuracy by 12.5 percentage
points. A single project authoring process can also produce repeated style
without exact duplicate text. The dataset can verify pipeline behavior and
compare lightweight candidates on a fixed split. It cannot estimate a
real-world false-positive rate or generalize to NCRP/I4C complaints.

The next dataset gate is at least 200 reviewed examples per fraud label plus
legitimate controls, with provenance, licensing, PII review, grouped splits,
and an unseen external source.

## Research Comparison

Published values below describe different datasets and tasks. This is not a shared leaderboard.

| System family | Evidence | Strength | Weakness | Relation to FraudLens |
|---|---|---|---|---|
| Manual review | No universal accuracy | Human context and judgment | Slow, inconsistent, hard to reproduce | Human review remains the final authority |
| Keyword rules | Local: 25.0% accuracy and Macro-F1 at 25% coverage | Cheap and auditable | Brittle phrasing and low coverage | Same frozen split baseline |
| Word TF-IDF | Local: 37.5% accuracy, 33.33% Macro-F1 | Small, fast, inspectable | Misspellings and Romanized variants fragment vocabulary | Same frozen split baseline |
| Character TF-IDF | Local: 75.0% accuracy, 66.67% Macro-F1 | Shares substrings across spelling and OCR noise | Larger than word features; weak semantics | Best parsimonious research candidate |
| Word-character TF-IDF | Local: 75.0% accuracy, 66.67% Macro-F1 | Combines two feature families | Same decisions as character-only at greater size | No measured gain on this split |
| Calibrated runtime | Local: 50.0% accuracy, 50.0% Macro-F1, 87.5% coverage | Better Brier score and explicit abstention | Accuracy fell with only 48 training rows | Deployed release model |
| HingRoBERTa complaint classifier [7] | Rani et al.: 74.41% accuracy and 71.49% F1 | Contextual Hinglish representation | Different I4C task/data; compute and fine-tuning cost | External context, not directly comparable |
| Neural phishing-URL detector [9] | Ghalechyan et al.: about 97% validation accuracy | Specialized URL scale and features | Binary URL task; label drift and narrow input | URL subsystem context, not directly comparable |
| Financial-fraud GNNs [10] | No universal comparable score | Learns relational patterns | Needs labelled temporal graphs and imbalance controls | Future research; FraudLens only visualizes repeats |

FraudLens cannot claim a more accurate classifier than external systems without
a shared dataset. Its stronger claim concerns the integrated student system: it
combines text and screenshot input, uncertainty, evidence extraction, reasons,
complaint drafting, consent, retention, masked relationships, reproducible
evaluation, and local CPU deployment.

### Named-solution evidence summary

Evidence labels prevent unlike facts from appearing as one leaderboard:

- **Measured locally** means generated on the frozen FraudLens split.
- **Verified capability** means implemented and covered by automated tests.
- **Externally reported** means stated by a named primary source on its own data.
- **Not yet measured** identifies a valid parameter without a FraudLens labelled
  benchmark.

| Named solution | Evidence and disclosed score | Scope | Defensible FraudLens advantage |
|---|---|---|---|
| National Cyber Crime Reporting Portal [2] | **Externally reported** official reporting capability; accuracy not applicable | Citizen complaint reporting | FraudLens structures evidence and prepares a draft before the user reports manually |
| Google Messages [15] | **Externally reported** on-device spam models and URL checking; accuracy **Not publicly disclosed** | Inbox warning, filtering, and spam reporting | FraudLens exposes eight-class triage, evidence fields, reasons, and complaint preparation after intake |
| HingRoBERTa [7] | **Externally reported** 74.41% accuracy and 71.49% F1 on I4C CyberGuard AI Hackathon data | Hinglish complaint classification with a Django REST/frontend tool | FraudLens adds screenshot OCR, explicit evidence, abstention, consented retention, and masked relationships; no external accuracy win is claimed |
| Neural phishing-URL detector [9] | **Externally reported** about 97% validation accuracy on a large binary URL task | Specialized URL classification and uncertainty | FraudLens analyzes the complete message or screenshot and uses URL checks as one auditable signal |
| Financial-fraud GNN research [10] | **Externally reported** review of more than 100 studies; no universal score | Learned detection over labelled relational graphs | FraudLens provides lightweight, privacy-safe repeated-entity visualization without claiming GNN detection |
| FraudLens Bharat | **Measured locally:** best research candidate 75.0% accuracy/66.67% Macro-F1; deployed runtime 50.0% accuracy/50.0% Macro-F1/87.5% coverage | End-to-end evidence triage | One reproducible workflow joins text, OCR, evidence, URL reasons, uncertainty, drafting, consent, expiry, and masked relationships |

The FraudLens and HingRoBERTa accuracy percentages occupy the same numerical
range, but different datasets and an eight-row synthetic FraudLens test mean
that this observation does not establish parity. The positive comparison rests
on measured same-split gains and documented workflow capabilities.

## Evaluation Parameters And Rationale

| Parameter | Why it belongs in the comparison |
|---|---|
| Accuracy | Familiar fraction of correct final decisions, but weak under imbalance |
| Macro-F1 | Primary metric; gives each fraud class equal weight |
| Balanced accuracy | Mean class recall; exposes majority-class dominance |
| Per-class precision and recall | Shows false alarms and missed high-harm categories |
| MCC | Correlation-style multiclass summary that remains useful under imbalance |
| Confusion matrix | Shows which scam types are confused |
| Coverage and abstention | Prevents selective models from hiding rejected inputs |
| Accepted accuracy | Measures correctness only on covered rows; must accompany coverage |
| ECE and Brier score | Measure whether confidence behaves like probability |
| Estimated fitted bytes | Supports a deterministic deployability comparison |
| OCR CER/WER | Measures transcription errors once a labelled screenshot set exists |
| Entity precision/recall/F1 | Separates false evidence from missed evidence |
| URL PR-AUC and false-positive rate | Fits an imbalanced detection subsystem better than accuracy alone |
| Graph edge precision/recall | Tests whether repeated-entity links are correct |
| Complaint human rubric | Measures completeness, correctness, actionability, hallucination, and privacy |
| p50/p95 latency and peak RAM | Measures practical local deployment with hardware and repetition disclosed |

The project does not compress these subsystem measures into one invented
“overall accuracy.” Each module needs labelled evidence suited to its task.

## Classification And Robustness Results

Character TF-IDF improves Macro-F1 over word TF-IDF by 0.3333 on the frozen
test. The pre-registered paired bootstrap interval is 0.0498 to 0.4084 across
2,000 resamples, with 97.7% positive differences. The interval describes these
eight rows; resampling cannot create missing authors, sources, benign examples,
or real OCR diversity.

The character and hybrid candidates remain at 0.6667 Macro-F1 under case and
punctuation changes, whitespace, Romanized spelling variants, and digit
masking. Both fall to 0.5833 under simulated OCR confusion. This supports
character features as a research direction, not as a replacement for a
labelled OCR benchmark.

The character model misses the digital-arrest test row as courier scam and the
OTP-phishing row as KYC scam. Those two classes have zero test F1. The deployed
calibrated model trades further classification quality for probability quality
and one abstention. The deck and demo keep these models separate.

### Data-backed Pareto position

| Advantage | Evidence status | Result |
|---|---|---|
| Strongest lightweight classification | **Measured locally** | Character Macro-F1 0.6667 versus word 0.3333 and rules 0.2500; gain over word = 0.3333 |
| Best research candidate by quality and size | **Measured locally** | Character and hybrid make the same decisions, but character uses 331,415 versus 415,954 estimated fitted bytes, 20.3% less |
| Best probability quality | **Measured locally** | Calibrated hybrid Brier 0.5894 versus 0.7908 for the uncalibrated hybrid, 25.5% lower, with lower accuracy disclosed |
| Complete review workflow | **Verified capability** | Text, screenshot OCR, entities, URL reasons, uncertainty, complaint draft, consent, expiry, and masked relationships pass automated behavior tests |
| Controlled subsystem quality | **Measured locally** | Entity micro-F1 0.9412 (n=40), URL F1 1.0000 (n=40), graph edge-F1 1.0000 (n=20), OCR CER 0.0792 and downstream label agreement 0.9167 (n=24), draft completeness 1.0000 (n=24) |
| Field accuracy and performance | **Not yet measured** | Naturally sourced OCR/entity/URL/graph labels, blinded human draft ratings, p50/p95 latency, peak RAM, and a usability study remain evaluation targets |

## Software Verification

The final local suite contains 369 automated tests across preprocessing,
training, inference trust boundaries, evaluation, research reproducibility,
entities, URL signals, risk, API, OCR, image policies, storage, retention,
privacy, graph analysis, website integration, deployment, and presentation
evidence.

GitHub Actions runs Python 3.10, canonical 3.11.15, and 3.12 plus a container
smoke test. CI regenerates the canonical model, evaluation, research outputs,
demo JSON, and presentation evidence. The container smoke checks readiness,
model analysis, English/Hindi OCR, safe logs, non-root execution, and the
read-only boundary.

## Privacy, Safety, And Human Control

- Storage defaults to off. The website requires explicit consent.
- Screenshot bytes never enter case storage.
- Retained text expires under the configured deadline.
- Relationship rows use HMAC IDs and masked labels rather than raw entities.
- Logs omit request bodies and concrete identifiers.
- The system makes no automatic filing, blocking, guilt, or legal decision.
- Human review required before any complaint or operational action.

## Threats To Validity

**Internal validity:** one synthetic authoring process may create repeated style.
Standard baselines reduce broad hyperparameter search, but they do not prove an
optimal model.

**Construct validity:** scam categories simplify real complaints. Accuracy does
not measure evidence correctness, complaint usefulness, legal fitness, or user
trust.

**External validity:** the data excludes benign messages, real complaints,
Devanagari, new sources, and temporal drift.

**Statistical validity:** eight test rows make scores discrete. Bootstrap
resampling describes sensitivity to those rows, not the wider population.

**Comparison validity:** the local text scores, published HingRoBERTa score,
phishing-URL score, and GNN literature answer different questions.

**Ethical validity:** false negatives may delay reporting; false positives may
cause fear. The release stays assistive and local.

## Conclusion And Future Work

FraudLens Bharat meets the planned software scope for a final college
prototype. It converts pasted or screenshot evidence into an explainable,
complaint-ready result and adds privacy controls that classifier-only demos
usually omit. The research benchmark identifies character TF-IDF as the most
promising lightweight representation on the present split.

### PPT-safe claims

- “On the same frozen test, character TF-IDF doubles Macro-F1 over word
  TF-IDF, from 0.3333 to 0.6667.”
- “The best research candidate matches the hybrid's test decisions with a
  20.3% smaller estimated fitted payload: 331,415 versus 415,954 bytes.”
- “Calibration produces the best Brier score, 0.5894, while the report exposes
  the corresponding accuracy trade-off.”
- “FraudLens combines evidence intake, review, uncertainty, privacy controls,
  and complaint preparation in one reproducible college prototype.”

Do not claim: FraudLens is more accurate than HingRoBERTa, Google Messages, a
production URL detector, or a GNN fraud platform.

The next work is empirical rather than cosmetic:

1. collect an authorized, diverse dataset with legitimate controls;
2. evaluate OCR CER/WER, entity F1, URL PR-AUC, graph edge quality, complaint
   quality, latency, and memory on labelled subsystem sets;
3. compare character TF-IDF and a Hinglish transformer on the same grouped
   external test;
4. run a supervised usability study and document error escalation;
5. add authentication and operational monitoring only if deployment expands
   beyond loopback local use.

## Reproducibility

```bash
PYTHONPATH=src python -m fraudlens.research_dataset \
  --dataset data/samples/phase2_dataset.csv \
  --output outputs/research/dataset_audit.json

PYTHONPATH=src python -m fraudlens.research_benchmark \
  --dataset data/samples/phase2_dataset.csv \
  --output outputs/research

PYTHONPATH=src python -m fraudlens.research_robustness \
  --dataset data/samples/phase2_dataset.csv \
  --output outputs/research \
  --bootstrap-samples 2000

PYTHONPATH=src python -m pytest -q
```

The machine-readable evidence lives in `outputs/phase2/`, `outputs/research/`,
and `outputs/presentation/`. The detailed methodology is in
`docs/research_methodology.md`; IEEE-style sources [1]-[16] are in
`docs/references.md`.

## Hybrid Evaluation Addendum

The final evidence package separates four questions rather than presenting one
misleading overall score: (1) the internal eight-class synthetic bootstrap,
(2) external binary spam/ham generalisation, (3) deployed-runtime behaviour on
held-out ham, and (4) subsystem quality.

The external benchmark uses the UCI SMS Spam Collection: 5,574 public messages,
grouped by normalized text before a deterministic 70/15/15 split. The 858-row
held-out test produced 98.60% accuracy, 0.9682 Macro-F1, 0.9273 spam recall and
0.0071 ECE for calibrated character TF-IDF. Character and word TF-IDF differed
by only +0.0023 Macro-F1 with a 95% paired-bootstrap interval of -0.0105 to
+0.0147, so the result is not statistically decisive. It is a binary task, not
the deployed eight-class score and not production accuracy.

Subsystem evidence is also explicit: 94.12% entity micro-F1 on 40 synthetic
cases; 100% URL-risk F1 on 40 controlled URLs; 100% graph edge-F1 on 20 cases
with zero raw-value leaks; and 24 real Tesseract screenshot runs with 0% OCR
failure, 7.92% CER and 91.67% downstream label agreement. Complaint drafts had
100% required-field completeness on 24 deterministic checks, which is not a
human quality rating. Aggregate JSON/CSV is committed; raw UCI messages,
row-level predictions and external fitted models are not.
