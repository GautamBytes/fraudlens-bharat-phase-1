# Comparative Analysis

## Purpose

This document explains how FraudLens Bharat should be compared with initial baselines and existing model families.

The key rule is fairness: do not compare a small synthetic Phase 1 split directly against large real-world transformer benchmarks as if the datasets were the same.

## Current Scope Context

> Current-scope note (2026-08-10): Phase 1 used a Streamlit demonstration interface. That interface is retired; the supported final product uses the Next.js website and FastAPI.

The comparisons below preserve Phase 1 baselines, but the current implementation
includes screenshot OCR and basic privacy-safe graph analytics. The graph links
repeated phone, UPI, email, and URL identifiers only across explicitly stored,
unexpired cases. It is observational, does not change classification or risk,
and does not perform production fraud-network detection or use a GNN.
Transformer comparison and GNN research remain future work.

## Comparison Questions

1. Is the Phase 1 prototype better than the initial manual/no-system state?
2. How does the selected calibrated baseline compare with the canonical rule fallback on the same frozen split?
3. How does Phase 1 compare with specialized published approaches?
4. Which metrics should be improved in Phase 2?

## Initial State Vs Phase 1

| Capability | Initial State | After Phase 1 |
|---|---|---|
| Input handling | Unstructured pasted text only in notes | Pasted text accepted through FastAPI and the now-retired Streamlit demonstration interface |
| Fraud taxonomy | No reproducible taxonomy | 8 fraud classes with labeling guide |
| Classification | Manual guesswork | Calibrated raw-normalized TF-IDF + Logistic Regression with explicit abstention |
| Evidence extraction | Manual reading | Regex extraction for phone, URL, UPI ID, email, money, OTP-like code, urgency, threat |
| URL risk | Manual inspection | Non-HTTPS, shortener, IP-host, suspicious keyword, and hyphenated-domain checks |
| Risk level | Not measured | Low/medium/high score with visible reasons |
| Complaint support | User writes from scratch | Complaint-ready draft generated for manual reporting |
| Metrics | None | Accuracy, precision, recall, F1, per-class report, confusion matrix |
| Reproducibility | Not reproducible | Seed dataset, tests, demo JSON, screenshots, model artifacts |
| Safety | Undefined | Synthetic data, no real PII requirement, no automatic complaint submission |

## Historical Rule-Only Vs Marker-Enhanced Hybrid Baseline

Both rows below use the earlier 64-row synthetic seed dataset and the same 16-row stratified test split. This is an archival Phase 1 comparison, not the current model result.

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Notes |
|---|---:|---:|---:|---:|---|
| Rule-only fallback | 0.8125 | 0.7917 | 0.8125 | 0.7833 | Useful as a safety fallback but misses some category phrasing |
| Historical marker-enhanced Phase 1 hybrid baseline | 1.0000 | 1.0000 | 1.0000 | 1.0000 | Superseded TF-IDF + Logistic Regression with transparent domain markers |

The historical improvement was caused by the model learning from text features while receiving explainable domain signals. It must not be compared with the current calibrated raw-normalized artifact, which uses frozen 48/8/8 splits. The implementation uses scikit-learn tooling for the reproducible TF-IDF and Logistic Regression baseline [12].

## Current Calibrated Artifact

The current source of truth is `models/model_metadata.json` and `models/metrics.json`. Its frozen 8-row synthetic test result is 0.5000 overall accuracy and raw macro-F1, 87.5% coverage, 12.5% abstention, and 57.14% accepted accuracy. The bootstrap has no legitimate examples, does not meet the 200-examples-per-label target, and is not production-ready.

The result should be described as an internal Phase 1 benchmark, not proof of real-world generalization.

## Before And After Model Quality

Earlier Phase 1 metrics were 0.875 accuracy and 0.875 macro-F1. The remaining errors were courier scam vs digital arrest confusion.

The revised preprocessing now avoids treating the Hinglish word "fir" as a police FIR by itself.

It also adds stronger transparent markers for parcel-number/drug-detection evidence and coercive FIR/video/payment evidence.

Historically, after marker enhancement, the same 16-row split reached 1.0000 accuracy and 1.0000 macro-F1. That superseded historical result is not comparable to the current calibrated artifact.

## Comparison With Published Hinglish Transformer Work

Rani et al. report HingRoBERTa at 74.41 percent accuracy and 71.49 percent F1 on I4C CyberGuard AI Hackathon data [7].

That is a larger and more realistic classification benchmark than this Phase 1 synthetic split.

FraudLens Bharat should not claim better general model performance from its historical 1.0000 internal score or its current synthetic bootstrap metrics.

The fair comparison is:

| Dimension | Hinglish Transformer Work | FraudLens Bharat Phase 1 |
|---|---|---|
| Primary goal | Complaint category classification | End-to-end text triage prototype |
| Dataset | I4C CyberGuard AI Hackathon data | 64-row synthetic seed dataset |
| Best cited metric | 74.41 percent accuracy, 71.49 percent F1 | Historical marker-enhanced 1.0000 internal accuracy/F1 on 16-row synthetic test split; superseded |
| Model type | Hinglish-adapted transformers | Current calibrated raw-normalized TF-IDF; historical markers superseded |
| Explainability | Not the main contribution | Visible entities, risk signals, complaint draft |
| Deployment artifact | Django REST/frontend tool | Phase 1: FastAPI, Streamlit, SQLite; final product: Next.js + FastAPI |
| Best use in this project | Phase 2 benchmark target | Phase 1 baseline and workflow proof |

## Comparison With URL-Only Phishing Models

Phishing URL research can train neural models on URL datasets and evaluate accuracy, precision, recall, F1, uncertainty, and latency [9].

FraudLens Bharat Phase 1 does not train a URL classifier. It applies auditable heuristics inside a broader triage pipeline.

| Dimension | URL-Only Model | FraudLens Bharat Phase 1 |
|---|---|---|
| Input | URL string | Full suspicious message |
| Output | Phishing/legitimate URL label | Fraud type, entities, risk level, complaint draft |
| Data need | Large URL datasets | Small seed text dataset plus rule checks |
| Explainability | Model confidence or uncertainty | Explicit URL risk signals |
| Phase 2 role | Candidate upgrade for URL scoring | Current heuristic baseline |

## Comparison With Graph Fraud Models

Graph fraud models are stronger when fraud is visible through relationships: repeated accounts, devices, UPI IDs, phone numbers, URLs, and transactions [10].

The historical Phase 1 snapshot extracted identifiers from one message at a
time. The current basic graph now links repeated phone, UPI, email, and URL
identifiers across retained, consented cases using masked labels and opaque
HMAC-backed identifiers.

The fair claim is limited to privacy-safe relationship visualization. This is
not a production fraud-network detector, a graph-learning system, or a GNN.

## Final Positioning

FraudLens Bharat Phase 1 is better than the initial manual baseline because it creates structured, explainable, reproducible triage output.

The historical marker-enhanced model outperformed the rule-only fallback on its 16-row synthetic split. The current calibrated bootstrap reports 0.5000 overall accuracy/raw macro-F1, 87.5% coverage, 12.5% abstention, and 57.14% accepted accuracy on a separate frozen 8-row split; it is not comparable and is not production-ready.

It is not yet better than mature transformer or graph systems on real-world external benchmarks.

The strongest Phase 1 claim is workflow completeness: classification, evidence extraction, URL checks, risk scoring, FastAPI, the retired demonstration interface, local storage, tests, and documentation in one prototype. The current final product exposes that workflow through the Next.js website and FastAPI.

## Phase 2 research benchmark

The final Phase 2 research benchmark adds rule-only, word TF-IDF, character
TF-IDF, word-character TF-IDF, and calibrated-hybrid candidates on the same
frozen split. Character and word-character candidates reach 0.7500 accuracy and
0.6667 macro-F1, compared with 0.3750 and 0.3333 for word TF-IDF. These values
come from the same eight-row synthetic test and are therefore suitable for an
internal ablation, not for declaring superiority over external transformer,
URL, or graph datasets. Full methods and limitations are in
`docs/phase2_research_report.md`.
