# FraudLens Bharat Phase 2 Research Report

## Abstract

FraudLens Bharat is an explainable, local-first prototype for triaging Indian
cyber-fraud messages written in English and Romanized Hinglish. It combines
message classification, evidence extraction, URL checks, screenshot OCR,
selective risk scoring, complaint-draft generation, opt-in local retention, and
privacy-safe repeated-identifier visualization. This study adds a reproducible
comparison of five lightweight classifier configurations on the project's
frozen 64-row synthetic dataset. Character TF-IDF and the word-character hybrid
each obtain 0.7500 accuracy and 0.6667 Macro-F1 on the eight-row frozen test,
compared with 0.3750 accuracy and 0.3333 Macro-F1 for word TF-IDF. The character
model's Macro-F1 difference from word TF-IDF is +0.3333, with a paired-bootstrap
95% interval of 0.0498 to 0.4084 under 2,000 resamples. Character-only matches
the hybrid's decisions with a 20.3% smaller estimated fitted payload. The
calibrated hybrid lowers Brier score by 25.5% against the uncalibrated hybrid,
with the corresponding accuracy loss reported. The strongest system result is
workflow breadth: one reproducible prototype joins message and screenshot
intake, evidence extraction, uncertainty, complaint preparation, consent,
retention, and masked relationships. The dataset remains synthetic, has no
legitimate examples, and has one test row per class, so the results support an
internal engineering advantage rather than production accuracy superiority.

## 1. Introduction

Indian cyber-fraud reports frequently begin as unstructured SMS, chat text,
URLs, payment identifiers, screenshots, or victim narratives. The language can
switch between English and Hindi within a sentence and Hindi is often written
in Roman script. A useful student system must therefore do more than assign a
label: it should preserve evidence, communicate uncertainty, respect privacy,
and help the user prepare a report without pretending to make a legal decision.

The implemented FraudLens Bharat release accepts text or PNG/JPEG screenshots,
classifies eight scam types, extracts common evidence entities, identifies
auditable URL risks, produces visible risk reasons, generates a complaint-ready
draft, and optionally stores a consented case. Repeated phone, UPI, email, and
URL identifiers can be viewed as masked relationships across retained cases.
The graph is observational and is not a GNN or a fraud-network detector.

The research problem is the difference between software completeness and model
evidence. The software has extensive automated tests and a hardened local
deployment, but the classifier dataset contains only 64 synthetic fraud
messages. This report measures what can be measured, describes what cannot yet
be claimed, and gives a fair comparison with representative existing solution
families.

## 2. Research Questions And Hypotheses

**RQ1.** Do character n-grams improve classification over word-only TF-IDF for
the frozen Hinglish/English scam-message split?

**H1.** Character TF-IDF will improve Macro-F1 because it can share evidence
across spelling variants, suffixes, transliterations, and partially corrupted
tokens.

**RQ2.** Does combining word and character features improve the result beyond
either representation alone?

**H2.** The hybrid will equal or exceed the best single representation, but its
larger feature space may not help on a very small dataset.

**RQ3.** Does sigmoid calibration improve probability quality without reducing
classification quality?

**H3.** Calibration will lower Expected calibration error and Brier score, but
three-fold calibration may reduce accuracy when only 48 training rows exist.

**RQ4.** How stable are the candidates under bounded language and OCR noise?

**H4.** Character features will lose less Macro-F1 than word-only features under
Romanized spelling and OCR-style substitutions.

**RQ5.** On which dimensions can FraudLens reasonably be considered better than
a classifier-only solution?

**H5.** Even without external accuracy superiority, FraudLens will demonstrate
broader end-to-end utility, local deployability, visible explanations,
selective prediction, and privacy controls.

## 3. Literature Selection Method

This is a structured scoping review, not a claim to enumerate every fraud
system ever published. Sources were selected from ACL Anthology, arXiv,
Scientific Reports, JMLR, NIST, official Indian-government publications, and
official product documentation when a deployed capability lacked a published
benchmark.
Search concepts covered *cybercrime complaint classification*, *Hinglish or
Hindi-English code-mixed classification*, *phishing URL detection*, *graph
financial fraud detection*, *explainable classification*, and *Indian digital
payment security*.

Sources were included when they described the task, model family, dataset or
data origin, and evaluation approach, or when they established authoritative
operational context. Duplicate summaries, promotional pages, and studies that
did not disclose enough methodology to interpret a metric were excluded from
the central comparison. Research published on a different label taxonomy or
dataset is discussed as external context and not a shared leaderboard.

The review covers representative families rather than claiming a complete
census. “Fraud detection” covers complaint text, URLs, transactions, accounts,
devices, and graphs. Their accuracy values answer different questions.

## 4. Existing Solution Families

### 4.1 Manual and rule-based triage

Manual review can use contextual knowledge and provide a human explanation, but
it is slow, inconsistent, and difficult to reproduce at scale. Keyword rules
are cheap and auditable but brittle under unseen phrasing, spelling changes, and
overlapping scam vocabulary. There is no universal published accuracy for
“manual” or “rule-based” fraud triage because performance depends on the rule
set, reviewer, taxonomy, and data.

On the same FraudLens frozen split, the canonical rules achieve 0.2500 accuracy
and 0.2500 Macro-F1 at 25% coverage. Accepted accuracy is 1.0000 because the
rules abstain on six of eight rows. This demonstrates why coverage must always
be reported beside accepted accuracy.

### 4.2 Classical word-based NLP

Bag-of-words and TF-IDF models are inexpensive, reproducible, and inspectable.
They work well when class-specific vocabulary repeats, but word features treat
many misspellings and Romanized variants as unrelated tokens and cannot model
long-range context.

FraudLens word_tfidf_logistic_regression achieves 0.3750 accuracy, 0.3333
Macro-F1, and 0.2965 MCC on the frozen split. It uses an estimated 85,083 bytes
of fitted numerical/vocabulary payload. Its main value is a strong transparent
baseline, not the best observed accuracy.

### 4.3 Character and hybrid classical NLP

Character n-grams can share substrings across informal spellings and OCR noise.
They cost more memory and can learn superficial patterns. The FraudLens
character_tfidf_logistic_regression result is 0.7500 accuracy, 0.7500 balanced
accuracy, 0.6667 Macro-F1, and 0.7412 MCC. The word-character hybrid produces
the same decisions and headline scores on this test. Therefore H1 is supported
internally, but H2 is not: adding word features did not improve the character
candidate on this split.

### 4.4 Generic and Hinglish-adapted transformers

Transformers model contextual token relationships and can benefit from
large-scale pretraining. Generic multilingual models may still be mismatched to
informal Romanized Hindi. HingBERT and HingRoBERTa were pretrained for
Hindi-English code mixing [7], [14]. Their weaknesses for a small college
prototype are training cost, model size, greater dependency complexity, and the
need for enough representative labelled text to fine-tune fairly.

Rani et al. used I4C CyberGuard AI Hackathon complaint data and reported their
best HingRoBERTa result at **74.41% accuracy and 71.49% F1** [7]. That study is
the closest published task comparison, but it uses a different dataset and task
taxonomy. Its percentages must not be placed beside FraudLens's eight-row
result as though they came from a shared test set.

### 4.5 Phishing URL models

URL systems classify URLs rather than complete fraud messages. They can use
lexical strings, DNS/host information, page content, or neural representations.
Ghalechyan et al. report about **97%** validation accuracy for neural
URL detection and discuss label quality, uncertainty, dataset drift,
and the impossibility of simple one-to-one comparison across unlike datasets
[9]. Their task is binary phishing-URL detection over hundreds of thousands of
URLs; FraudLens URL heuristics are one auditable signal inside a larger triage
workflow. This is a different dataset and task, not a shared leaderboard.

### 4.6 Graph-based fraud detection

Graph methods represent relationships among accounts, cards, devices, phone
numbers, merchants, URLs, and transactions. GNNs can learn patterns unavailable
to independent-row classifiers, but require a meaningful graph, fraud labels,
temporal validation, severe-imbalance controls, and drift monitoring. The review
by Cheng et al. covers more than 100 studies and stresses the variety of graph
tasks and datasets [10]. A single “GNN accuracy” would therefore be misleading.

FraudLens only shows repeated masked identifiers across consented retained
cases. It has no labelled fraud-network data and makes no GNN accuracy claim.

### 4.7 Explainable and end-to-end systems

LIME demonstrated why users may need local reasons before trusting a classifier
[11]. NIST AI RMF emphasizes validity, reliability, transparency,
explainability, privacy, and accountability [13]. FraudLens uses directly
visible evidence entities and rule contributions rather than a post-hoc neural
explanation. The approach is less expressive than a learned explanation model
but easier to audit for this prototype.

| Family | Typical strength | Typical weakness | Published or local evidence | Fair relation to FraudLens |
|---|---|---|---|---|
| Manual review | Context and human judgment | Slow, inconsistent, not reproducible | No universal accuracy | Motivation for assistive triage |
| Keyword rules | Cheap and transparent | Brittle, low coverage | Local 0.2500 Macro-F1 at 25% coverage | Same-split baseline |
| Word TF-IDF | Fast and interpretable | Weak to spelling/code-mix variation | Local 0.3333 Macro-F1 | Same-split baseline |
| Character TF-IDF | Robust lexical subpatterns | Larger feature space, limited semantics | Local 0.6667 Macro-F1 | Best same-split lightweight result |
| Hinglish transformers | Context and code-mixed pretraining | Compute/data cost, harder deployment | HingRoBERTa 74.41% accuracy, 71.49% F1 [7] | External task benchmark only |
| Neural phishing URL detection | Strong specialized binary detection | Narrow input and drift/label concerns | About 97% in [9] | Separate subsystem task |
| Graph/GNN fraud detection | Relational patterns | Requires labelled temporal graph | No universal comparable score [10] | Future research, not implemented |
| FraudLens workflow | Classification plus evidence, OCR, privacy and deployment | Small synthetic classifier dataset | 0.7500 best internal accuracy | System contribution, not external superiority |

## 5. Named Solution Comparison

The comparison uses four evidence labels throughout this report:

- **Measured locally:** generated from the frozen FraudLens dataset by committed
  code.
- **Verified capability:** implemented behavior covered by automated tests, but
  not a labelled accuracy benchmark.
- **Externally reported:** a result or capability stated by the named primary
  source on its own task and data.
- **Not yet measured:** a relevant parameter for which FraudLens has no labelled
  evaluation set.

| Named solution | Primary task and evidence | Disclosed result | Documented scope | Data-backed FraudLens position |
|---|---|---|---|---|
| National Cyber Crime Reporting Portal [2] | Official complaint reporting; **Externally reported** capability | Not publicly disclosed | Accepts citizen cybercrime reports and supports the operational reporting process | FraudLens prepares structured, human-reviewable evidence before manual reporting; it does not replace or submit to NCRP |
| Google Messages spam protection [15] | Message spam/scam filtering and URL checking; **Externally reported** capability | Not publicly disclosed | Uses on-device ML for known spam patterns and can send URLs for malicious-link checks | FraudLens documents an eight-class triage result, extracted evidence, reasons, and a complaint draft after intake; no spam-detection accuracy comparison is possible |
| HingRoBERTa complaint classifier [7] | Hinglish cybercrime complaint classification on I4C CyberGuard AI Hackathon data; **Externally reported** result | 74.41% accuracy; 71.49% F1 | Contextual classification, privacy-aware preprocessing, augmentation, Django REST and a frontend | FraudLens adds OCR, explicit evidence fields, URL reasons, abstention, consented retention, and masked relationships; it does not establish an accuracy win |
| Ghalechyan et al. neural URL detector [9] | Binary URL classification over large open and production datasets; **Externally reported** result | About 97% validation accuracy | Specialized deterministic/probabilistic URL models with uncertainty analysis | FraudLens accepts a complete message or screenshot and treats URL checks as one visible signal; it does not match the URL detector's scale or claim its accuracy |
| Cheng et al. graph-fraud review [10] | Review of more than 100 financial-fraud GNN studies; **Externally reported** research context | No universal comparable score | Learned detection over labelled account, transaction, device, and other graphs | FraudLens offers CPU-friendly masked repeated-entity visualization; it does not perform GNN fraud detection |
| FraudLens Bharat | Eight-class message triage and end-to-end evidence review; **Measured locally** plus **Verified capability** | Best research candidate: 75.0% accuracy and 66.67% Macro-F1 on eight synthetic test rows; deployed runtime: 50.0% accuracy, 50.0% Macro-F1, 87.5% coverage | Text and screenshot intake, evidence extraction, URL reasons, uncertainty, complaint drafting, consent, retention, and masked relationships | Strongest evidence concerns workflow breadth, inspectability, privacy controls, reproducibility, and local deployment |

The FraudLens 75.0% research accuracy and HingRoBERTa 74.41% accuracy sit in the
same numerical range. The comparison does not establish parity: FraudLens uses
eight synthetic test rows, while HingRoBERTa uses a different I4C-derived task,
dataset, taxonomy, and evaluation protocol. The table therefore compares
published evidence and workflow scope rather than manufacturing a leaderboard.

## 6. Research Gap And Proposed Contribution

Most compared studies optimize one technical task: complaint classification,
URL classification, or relational fraud detection. FraudLens studies a narrower
research gap: whether a small, explainable, locally deployable pipeline can turn
messy Indian scam evidence into structured and reviewable triage output while
communicating uncertainty and preserving consent.

The proposed contribution has three parts:

1. a reproducible same-split benchmark that prevents fit/threshold leakage;
2. an explainable end-to-end implementation spanning text, screenshots,
   entities, URLs, risk signals, case retention, and masked relationships; and
3. explicit validity boundaries that prevent a synthetic result from being
   marketed as real-world accuracy.

“Better” is conditional. FraudLens is a better classifier only if it wins on the
same test with uncertainty reported. It can be a better student system when its
accuracy is competitive and it provides broader workflow, privacy,
explainability, reproducibility, and CPU deployability. This report supports the
second claim more strongly than the first.

## 7. Dataset And Ethics

The research CSV contains **64 synthetic**, manually reviewed messages: 48
train, 8 validation, and an **eight-row frozen test**. There are eight examples
per fraud class, 36 English rows, and 28 Hinglish rows. There are **no legitimate**
messages and no real victim PII. All rows share one project-generated provenance
source, although every template group remains inside one split and the audit
finds no normalized duplicate group.

These properties make the dataset appropriate for pipeline verification but
weak for empirical generalization. The missing legitimate class prevents false
positive analysis on benign messages. One test row per present class makes a
single mistake change accuracy by 12.5 percentage points. Synthetic language
may repeat author style and may not reproduce real spelling, emotion, missing
context, or adversarial behavior.

A defensible next dataset should contain at least 200 examples per label across
the eight scam classes and legitimate controls, with explicit provenance,
licensing, PII review, independent template/source groups, and an unseen
external test source. Private I4C complaints must not be downloaded or
redistributed without authorization.

## 8. Experimental Methodology

The exact protocol is documented in `docs/research_methodology.md`. All fitted
features and coefficients use train only. Validation selects the confidence
threshold. Test is evaluated once. Random seed 42 is fixed. Every final
abstention becomes `unknown` and counts as an overall error.

The primary metric is Macro-F1 because every fraud class matters equally.
Accuracy, balanced accuracy, precision, recall, weighted F1, MCC, coverage,
accepted accuracy, ECE, Brier score, per-class scores, and the confusion matrix
provide complementary evidence. Canonical outputs exclude wall-clock timing so
CI can compare them byte-for-byte; any later latency experiment must record the
hardware and repetition protocol.

Robustness uses deterministic case/punctuation, whitespace, Hinglish spelling,
digit-masking, and OCR confusion transformations. Statistical comparison uses
the pre-registered H1 pair—character TF-IDF versus word TF-IDF—rather than a
winner selected from the frozen test. It uses 2,000 paired bootstrap samples of
the same eight test indices and a percentile 95% confidence interval for the
Macro-F1 difference.

## 9. Classification Results

| Candidate | Accuracy | Balanced accuracy | Macro-F1 | MCC | Coverage | Accepted accuracy | ECE | Brier | Estimated bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rule_only | 0.2500 | 0.2500 | 0.2500 | 0.3669 | 0.2500 | 1.0000 | N/A | N/A | 0 |
| word_tfidf_logistic_regression | 0.3750 | 0.3750 | 0.3333 | 0.2965 | 1.0000 | 0.3750 | 0.2635 | 0.8290 | 85,083 |
| character_tfidf_logistic_regression | **0.7500** | **0.7500** | **0.6667** | **0.7412** | 1.0000 | 0.7500 | 0.5865 | 0.8176 | 331,415 |
| word_character_tfidf_logistic_regression | **0.7500** | **0.7500** | **0.6667** | **0.7412** | 1.0000 | 0.7500 | 0.6248 | 0.7908 | 415,954 |
| calibrated_word_character_tfidf | 0.5000 | 0.5000 | 0.5000 | 0.4364 | 1.0000 | 0.5000 | 0.2804 | **0.5894** | 969,536 |

Character features produce the strongest observed classification result and a
0.3333 Macro-F1 increase over word-only TF-IDF.
The hybrid makes exactly the same eight test decisions, so its additional word
feature payload is not justified by this split. The character-only candidate is
therefore the preferred research result on parsimony grounds.

Calibration provides the best Brier score and a much smaller ECE than either
uncalibrated character candidate, but its accuracy falls to 0.5000. This rejects
the accuracy part of H3 while supporting its probability-quality part. With 48
training rows, three-fold calibration fits on very small folds and should be
revisited only after dataset expansion.

### Local Pareto advantages

| Supported claim | Evidence status | Data |
|---|---|---|
| Character features improve the lightweight baseline | **Measured locally** | Macro-F1 0.6667 versus 0.3333 for word TF-IDF and 0.2500 for rules |
| Character-only is the best research candidate on parsimony | **Measured locally** | Same eight predictions as the hybrid at 331,415 versus 415,954 estimated fitted bytes, a 20.3% smaller payload |
| Calibration improves probability quality | **Measured locally** | Brier score 0.5894 versus 0.7908 for the uncalibrated hybrid, 25.5% lower; accuracy falls from 0.7500 to 0.5000 |
| The deployed runtime communicates uncertainty | **Measured locally** | 87.5% coverage, 12.5% abstention, and 57.14% accepted accuracy on the release evaluation |

These results support a Pareto claim: no candidate wins every parameter.
Character-only offers the strongest measured quality/size trade-off, while the
deployed runtime prioritizes calibrated confidence and abstention.

### Error analysis

The character model correctly classifies courier, fake job, investment, KYC,
loan, and UPI refund rows. The digital_arrest row is predicted as courier scam,
and the otp_phishing row is predicted as KYC scam. Consequently,
`digital_arrest` and `otp_phishing` each have zero test F1 despite the 0.7500
overall accuracy. Those are high-value regression targets for future data
collection. No legitimate false-positive rate can be measured because the
class is absent.

## 10. Robustness And Ablation Results

| Candidate | Clean Macro-F1 | Case/punctuation | Whitespace | Hinglish spelling | Digit masking | OCR confusion |
|---|---:|---:|---:|---:|---:|---:|
| Rules | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.1250 |
| Word TF-IDF | 0.3333 | 0.5000 | 0.3333 | 0.3333 | 0.3333 | 0.3333 |
| Character TF-IDF | **0.6667** | 0.6667 | 0.6667 | 0.6667 | 0.6667 | 0.5833 |
| Word-character TF-IDF | **0.6667** | 0.6667 | 0.6667 | 0.6667 | 0.6667 | 0.5833 |
| Calibrated hybrid | 0.5000 | 0.5833 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |

Character and hybrid candidates are unchanged under four controlled conditions
and lose 0.0833 Macro-F1 under **OCR confusion**. This supports H4 only for the
simulated conditions. Word TF-IDF unexpectedly improves after punctuation
removal; with one row per class, one changed decision can create that result.
Negative “drop” values in the machine-readable evidence therefore mean an
observed improvement, not a data error.

The ablation shows that character features, rather than combining feature
families, explain the observed gain. Calibration changes probability quality
and decisions but does not improve the best headline result.

## 11. Full-System Evaluation Framework

Classification accuracy is not a sufficient measure of the complete system.
The following parameters should be measured on labelled subsystem datasets:

| Subsystem | Parameters | Why they make sense | Current evidence boundary |
|---|---|---|---|
| OCR | Character error rate, word error rate, downstream Macro-F1 drop | Measures transcription quality and whether OCR errors change decisions | Automated behavior tests; no labelled screenshot corpus |
| Entity extraction | Per-type precision/recall/F1 and normalized exact match | Separates false evidence from missed evidence | Regression tests for phone, UPI, URL, email, money and codes |
| URL analysis | Precision, recall, PR-AUC, false-positive rate at fixed recall | Fraud URLs are often imbalanced; accuracy alone can hide misses | Auditable heuristics, no URL benchmark claim |
| Graph linking | Edge precision/recall/F1 and top-k case-link precision | Measures whether repeated entities connect the correct cases | Deterministic masked-link tests, no fraud-node labels |
| Risk scoring | Sensitivity by severity band and reason completeness | Risk is a policy score rather than a pure class label | Boundary and explanation tests |
| Complaint draft | Human rubric for completeness, correctness, actionability, hallucination and privacy | Text quality requires structured review | Template-contract tests only |
| Deployment | p50/p95 latency, peak RAM, fitted bytes, offline capability | Measures whether the system is practical on student hardware | Estimated fitted bytes; environment timing deferred |

These are separate tasks and must not be collapsed into one arbitrary “overall
accuracy.” A Pareto comparison is preferable: show where one system is more
accurate, smaller, faster, more private, or more complete.

| Project statement | Evidence status | What may be claimed now |
|---|---|---|
| Same-split model quality, robustness, calibration, and fitted size | **Measured locally** | Exact values from deterministic research artifacts |
| Text/screenshot intake, entities, URL reasons, complaint draft, consent, expiry, and masked relationships | **Verified capability** | Implemented and covered by automated tests; no subsystem accuracy percentage |
| HingRoBERTa, Google Messages, neural URL detection, and GNN research | **Externally reported** | Only the task, capability, dataset, and metric disclosed by each primary source |
| OCR CER/WER, entity F1, URL PR-AUC, graph edge F1, human draft quality, p50/p95 latency, and peak RAM | **Not yet measured** | Evaluation parameters and future work, not completed results |

## 12. Statistical Interpretation

The pre-registered H1 comparison uses character TF-IDF against word TF-IDF; it
does not select a winner after inspecting the frozen test results. Character
TF-IDF has a Macro-F1 point advantage of **+0.3333**. The paired bootstrap 95%
interval is **0.0498 to 0.4084**, and 97.7% of the 2,000 resamples give a
positive difference. On this fixed split, that supports the claim that
character features help.

The result remains fragile. Bootstrap resampling cannot create diversity absent
from the eight original observations. The narrow-looking positive lower bound
does not account for different authors, sources, time periods, legitimate
messages, or real OCR. The correct conclusion is “promising internal evidence,”
not “FraudLens outperforms HingRoBERTa” or “75% production accuracy.”

## 13. Explainability, Privacy, And Deployment

FraudLens exposes detected entities and visible risk reasons rather than asking
the user to trust a label alone. Predictions can abstain, although the research
thresholds accept all rows for the trainable candidates on this validation
split. These research candidates do not replace the selected runtime model.
The system defaults to no storage, requires explicit website consent,
does not retain screenshot bytes, applies retention deadlines, masks graph
labels, and uses opaque HMAC-backed entity identifiers.

The release is runnable locally through the Next.js website and FastAPI and has
a pinned, non-root, read-only container configuration. Structured request logs exclude
bodies and concrete identifiers. These properties support the end-to-end and
privacy contribution, but software hardening does not establish production
accuracy.

## 14. Threats To Validity

**Internal validity.** One authoring process may create repeated style even
without exact duplicates. Hyperparameters were chosen as standard lightweight
baselines rather than through a broad search, reducing test overfitting but not
guaranteeing optimal models.

**Construct validity.** Synthetic scam categories simplify real complaints.
Accuracy does not measure entity correctness, complaint usefulness, legal
appropriateness, user trust, or actual fraud prevention.

**External validity.** The dataset has no real complaints, no legitimate
controls, no Devanagari rows, one provenance source, and no temporal drift.
Results cannot be generalized to NCRP/I4C traffic or other regions.

**Statistical conclusion validity.** Eight test observations make every metric
discrete and unstable. Paired bootstrap describes sensitivity to resampling
these rows, not uncertainty over the wider population.

**Comparison validity.** The published 74.41% HingRoBERTa accuracy, 97% URL
accuracy, local 75% character-model accuracy, and GNN studies use different
tasks and datasets. They are not interchangeable rankings.

**Ethical validity.** A false negative may delay reporting; a false positive may
create unnecessary fear. The system remains assistive, requires human review,
and does not automatically file a complaint or block a transaction.

## 15. PPT-safe claims

Use these statements in the presentation:

- **Measured locally:** “Character TF-IDF doubled Macro-F1 over word TF-IDF,
  from 0.3333 to 0.6667, on the same frozen test.”
- **Measured locally:** “Character-only matched the larger hybrid's decisions
  with a 20.3% smaller estimated fitted payload.”
- **Measured locally:** “Calibration reduced the hybrid Brier score by 25.5%,
  while exposing a clear accuracy trade-off.”
- **Verified capability:** “FraudLens combines message and screenshot intake,
  evidence extraction, uncertainty, complaint preparation, consent, retention,
  and masked relationships in one reproducible college prototype.”
- **Externally contextualized:** “Our best internal headline accuracy lies in
  the same numerical range as the cited HingRoBERTa result, but different data
  and an eight-row synthetic test prevent a parity or superiority claim.”

Do not claim: FraudLens is more accurate than HingRoBERTa, Google Messages, a
production URL detector, or a GNN fraud platform.

## 16. Conclusion

The coded benchmark answers the narrow internal question: character TF-IDF is
the strongest lightweight candidate on the current frozen split, reaching
0.7500 accuracy and 0.6667 Macro-F1 and remaining stable under four controlled
noise conditions. Word-character fusion does not improve it, while calibration
improves probability quality but reduces classification accuracy.

The result does not establish production accuracy. The strongest defensible
claim is that FraudLens Bharat is a reproducible, explainable, privacy-aware,
end-to-end college prototype with promising character-level classification
evidence. Against the measured local baselines it offers the best quality/size
trade-off, and against the named external systems it documents a broader
evidence-review workflow without borrowing their accuracy claims. The next
empirical requirement is an ethically sourced dataset of at
least 200 reviewed examples per fraud label plus legitimate controls, followed
by the same grouped protocol and a same-data Hinglish-transformer comparison.

## Reproduction Commands

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

Compact evidence is committed under `outputs/research/`. The full
`classification_benchmark.json` and `robustness_benchmark.json` diagnostics are
generated locally but ignored by Git. CI creates two independent runs,
byte-compares every JSON and CSV artifact between them, and compares the compact
committed evidence with the generated result. References [1]-[15] are listed in
`docs/references.md`.
