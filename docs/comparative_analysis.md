# Comparative Analysis

## Purpose

This document explains how FraudLens Bharat should be compared with initial baselines and existing model families.

The key rule is fairness: do not compare a small synthetic Phase 1 split directly against large real-world transformer benchmarks as if the datasets were the same.

## Comparison Questions

1. Is the Phase 1 prototype better than the initial manual/no-system state?
2. Is the hybrid baseline better than the rule-only fallback on the same seed split?
3. How does Phase 1 compare with specialized published approaches?
4. Which metrics should be improved in Phase 2?

## Initial State Vs Phase 1

| Capability | Initial State | After Phase 1 |
|---|---|---|
| Input handling | Unstructured pasted text only in notes | Pasted text accepted through API and dashboard |
| Fraud taxonomy | No reproducible taxonomy | 8 fraud classes with labeling guide |
| Classification | Manual guesswork | Hybrid TF-IDF + Logistic Regression classifier |
| Evidence extraction | Manual reading | Regex extraction for phone, URL, UPI ID, email, money, OTP-like code, urgency, threat |
| URL risk | Manual inspection | Non-HTTPS, shortener, IP-host, suspicious keyword, and hyphenated-domain checks |
| Risk level | Not measured | Low/medium/high score with visible reasons |
| Complaint support | User writes from scratch | Complaint-ready draft generated for manual reporting |
| Metrics | None | Accuracy, precision, recall, F1, per-class report, confusion matrix |
| Reproducibility | Not reproducible | Seed dataset, tests, demo JSON, screenshots, model artifacts |
| Safety | Undefined | Synthetic data, no real PII requirement, no automatic complaint submission |

## Rule-Only Vs Hybrid Baseline

Both rows below use the same 64-row synthetic seed dataset and the same 16-row stratified test split.

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Notes |
|---|---:|---:|---:|---:|---|
| Rule-only fallback | 0.8125 | 0.7917 | 0.8125 | 0.7833 | Useful as a safety fallback but misses some category phrasing |
| Phase 1 hybrid baseline | 1.0000 | 1.0000 | 1.0000 | 1.0000 | TF-IDF + Logistic Regression with transparent domain markers |

The improvement is caused by the model learning from text features while still receiving explainable domain signals.

The result should be described as an internal Phase 1 benchmark, not proof of real-world generalization.

## Before And After Model Quality

Earlier Phase 1 metrics were 0.875 accuracy and 0.875 macro-F1. The remaining errors were courier scam vs digital arrest confusion.

The revised preprocessing now avoids treating the Hinglish word "fir" as a police FIR by itself.

It also adds stronger transparent markers for parcel-number/drug-detection evidence and coercive FIR/video/payment evidence.

After retraining, the same split reaches 1.0000 accuracy and 1.0000 macro-F1.

## Comparison With Published Hinglish Transformer Work

Rani et al. report HingRoBERTa at 74.41 percent accuracy and 71.49 percent F1 on I4C CyberGuard AI Hackathon data.

That is a larger and more realistic classification benchmark than this Phase 1 synthetic split.

FraudLens Bharat should not claim better general model performance from its 1.0000 internal score.

The fair comparison is:

| Dimension | Hinglish Transformer Work | FraudLens Bharat Phase 1 |
|---|---|---|
| Primary goal | Complaint category classification | End-to-end text triage prototype |
| Dataset | I4C CyberGuard AI Hackathon data | 64-row synthetic seed dataset |
| Best cited metric | 74.41 percent accuracy, 71.49 percent F1 | 1.0000 internal accuracy/F1 on 16-row synthetic test split |
| Model type | Hinglish-adapted transformers | TF-IDF + Logistic Regression with transparent markers |
| Explainability | Not the main contribution | Visible entities, risk signals, complaint draft |
| Deployment artifact | Django REST/frontend tool | FastAPI, Streamlit, SQLite |
| Best use in this project | Phase 2 benchmark target | Phase 1 baseline and workflow proof |

## Comparison With URL-Only Phishing Models

Phishing URL research can train neural models on URL datasets and evaluate accuracy, precision, recall, F1, uncertainty, and latency.

FraudLens Bharat Phase 1 does not train a URL classifier. It applies auditable heuristics inside a broader triage pipeline.

| Dimension | URL-Only Model | FraudLens Bharat Phase 1 |
|---|---|---|
| Input | URL string | Full suspicious message |
| Output | Phishing/legitimate URL label | Fraud type, entities, risk level, complaint draft |
| Data need | Large URL datasets | Small seed text dataset plus rule checks |
| Explainability | Model confidence or uncertainty | Explicit URL risk signals |
| Phase 2 role | Candidate upgrade for URL scoring | Current heuristic baseline |

## Comparison With Graph Fraud Models

Graph fraud models are stronger when fraud is visible through relationships: repeated accounts, devices, UPI IDs, phone numbers, URLs, and transactions.

Phase 1 only extracts identifiers from one message at a time. It does not yet model relationships across cases.

The fair claim is that Phase 1 creates graph-ready evidence, while Phase 2 should connect repeated identifiers into a fraud network.

## Final Positioning

FraudLens Bharat Phase 1 is better than the initial manual baseline because it creates structured, explainable, reproducible triage output.

It is better than the rule-only fallback on the current seed split because the hybrid model improves measured accuracy and macro-F1.

It is not yet better than mature transformer or graph systems on real-world external benchmarks.

The strongest Phase 1 claim is workflow completeness: classification, evidence extraction, URL checks, risk scoring, API/dashboard, local storage, tests, and documentation in one prototype.
