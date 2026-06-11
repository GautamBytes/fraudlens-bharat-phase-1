# Literature Review

## Purpose

This review explains why FraudLens Bharat is framed as a cyber-fraud triage system, not only a text classifier.

Phase 1 connects five research areas: Indian cybercrime reporting, Hinglish complaint classification, phishing URL analysis, explainable AI, and future graph analytics.

## Indian Cyber-Fraud Reporting Context

The Ministry of Home Affairs describes cybercrime handling as a coordinated system involving I4C, NCRP, CFCFRMS, 1930, banks, payment aggregators, telecom providers, and state law enforcement.

PIB reported 29,44,248 cyber security incidents tracked by CERT-In for 2025. It also reported 86,420 registered cybercrime cases in NCRB's latest published 2023 data.

The same PIB release states that CFCFRMS saved more than Rs. 8,690 crore across more than 24.65 lakh complaints up to 31 January 2026.

This context supports the project motivation: early, structured evidence capture can matter because reporting speed and evidence quality affect fraud response.

Phase 1 does not integrate with government systems. It prepares a complaint-ready draft and preserves user control.

## Hinglish And Code-Mixed Complaint Classification

Recent research on cybercrime complaint classification highlights that Indian complaints are often multilingual and code-mixed.

Rani et al. used Hinglish-adapted transformer models, including HingBERT and HingRoBERTa, on I4C CyberGuard AI Hackathon data.

Their HingRoBERTa result reached 74.41 percent accuracy and 71.49 percent F1 score. That is a useful external benchmark for future Phase 2 transformer work.

FraudLens Bharat does not claim to outperform transformer systems on real-world I4C data. Phase 1 instead proves a reproducible local baseline with explainable signals.

## Phishing URL Detection

Phishing URL detection research shows that URL-only models can reach strong results when trained on large URL datasets.

The Scientific Reports 2024 study compared deterministic and probabilistic neural network models for phishing URL detection.

It found that uncertainty-aware probabilistic outputs improved accuracy by around 4 percent and helped explain uncertain URL predictions.

FraudLens Bharat uses simpler Phase 1 URL heuristics: non-HTTPS links, shorteners, IP hostnames, suspicious URL keywords, and hyphenated domains.

This is less powerful than a trained URL model but easier to audit and run locally during Phase 1.

## Graph-Based Fraud Detection

Graph Neural Networks are widely studied for financial fraud because fraud often depends on relationships among accounts, phone numbers, devices, URLs, and transactions.

Cheng et al. reviewed over 100 studies on GNNs for financial fraud detection and described their strength in modeling relational patterns.

FraudLens Bharat does not implement graph analytics in Phase 1. The entity extraction output creates a path toward Phase 2 graph work.

The natural Phase 2 graph would connect repeated UPI IDs, phone numbers, URLs, emails, complaint categories, timestamps, and risk outcomes.

## Explainability And Trust

Ribeiro, Singh, and Guestrin argued that explanations are important when people need to decide whether to trust a classifier.

Their LIME work motivates a broader design principle: predictions should be paired with reasons that a user can inspect.

FraudLens Bharat follows this principle through visible entities, risk signals, confidence, and a complaint draft.

The current explanation method is rule-based rather than LIME-based. That is acceptable for Phase 1 because each score contribution is explicit.

## Research Gap Addressed By Phase 1

Most published systems focus on a single technical task such as classification, URL detection, or graph fraud modeling.

FraudLens Bharat combines a small classifier, entity extraction, URL checks, risk scoring, local storage, API access, and a dashboard into one reproducible student prototype.

The contribution is not state-of-the-art model performance. The contribution is an explainable end-to-end triage workflow for Indian Hinglish cyber-fraud messages.

## Sources

1. Ministry of Home Affairs, Press Information Bureau, "Assistance to States to Tackle Cyber Incidents," 24 March 2026. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2244504&lang=1&reg=3
2. National Cyber Crime Reporting Portal, Government of India. https://www.cybercrime.gov.in/
3. N. Rani, D. Singh, B. Saha, and S. K. Shukla, "Automated Classification of Cybercrime Complaints using Transformer-based Language Models for Hinglish Texts," arXiv:2412.16614, 2024. https://arxiv.org/abs/2412.16614
4. K. Stepanyan et al., "Phishing URL detection with neural networks: an empirical study," Scientific Reports, 2024. https://www.nature.com/articles/s41598-024-74725-6
5. D. Cheng, Y. Zou, S. Xiang, and C. Jiang, "Graph Neural Networks for Financial Fraud Detection: A Review," arXiv:2411.05815, 2024. https://arxiv.org/abs/2411.05815
6. M. T. Ribeiro, S. Singh, and C. Guestrin, "'Why Should I Trust You?': Explaining the Predictions of Any Classifier," KDD, 2016. https://arxiv.org/abs/1602.04938
