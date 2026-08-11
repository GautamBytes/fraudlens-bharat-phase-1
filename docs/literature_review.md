# Literature Review

## Purpose

This review explains why FraudLens Bharat is framed as a cyber-fraud triage system, not only a text classifier.

Phase 1 connects six research areas: Indian cybercrime reporting, digital payment security, Hinglish complaint classification, phishing URL analysis, explainable AI, and graph-based fraud research.

The current implementation includes screenshot OCR and basic privacy-safe graph
analytics beyond that Phase 1 snapshot. Transformer comparison and GNN research
remain future work.

## Indian Cyber-Fraud Reporting Context

The Ministry of Home Affairs describes cybercrime handling as a coordinated system involving I4C, NCRP, CFCFRMS, 1930, banks, payment aggregators, telecom providers, and state law enforcement [1].

PIB reported 29,44,248 cyber security incidents tracked by CERT-In for 2025. It also reported 86,420 registered cybercrime cases in NCRB's 2023 data [1]. NCRB's publication portal is the official source for year-wise Crime in India reports [3].

The same PIB release states that CFCFRMS saved more than Rs. 8,690 crore across more than 24.65 lakh complaints up to 31 January 2026 [1].

CERT-In's 2022 directions also show why timestamps, logs, incident categories, phishing indicators, and digital-payment incident evidence matter for cyber incident response [4].

This context supports the project motivation: early, structured evidence capture can matter because reporting speed and evidence quality affect fraud response. Phase 1 does not integrate with government systems. It prepares a complaint-ready draft and preserves user control.

## Digital Payment And UPI Safety Context

Many target scam categories involve UPI, bank accounts, KYC, OTPs, payment links, refund requests, and transaction pressure.

The RBI Master Direction on Digital Payment Security Controls requires regulated entities to manage digital-payment fraud risk, educate customers, provide grievance channels, and support early fraud reporting [5].

NPCI's UPI product context supports why UPI IDs, collect requests, payment references, and user-facing payment flows are treated as important evidence fields [6].

FraudLens Bharat does not process live payments. It only extracts and structures evidence that a user can manually review.

## Hinglish And Code-Mixed Complaint Classification

Recent research on cybercrime complaint classification highlights that Indian complaints are often multilingual and code-mixed [7].

Rani et al. used Hinglish-adapted transformer models, including HingBERT and HingRoBERTa, on I4C CyberGuard AI Hackathon data [7].

Their HingRoBERTa result reached 74.41 percent accuracy and 71.49 percent F1 score. That is a useful external benchmark for future Phase 2 transformer work [7].

Kapoor et al. also show that Hinglish code-switched text is difficult because spelling, grammar, vocabulary, and semantics are less fixed than in monolingual text [8].

FraudLens Bharat does not claim to outperform transformer systems on real-world I4C data. Phase 1 instead proves a reproducible local baseline with explainable signals.

## Deployed Message Spam Protection

Google Messages documents a deployed spam-protection workflow that uses
on-device machine-learning models to detect known spam patterns and can send a
message URL to Google for a malicious-link check [15]. The product can warn,
filter, and support spam reporting. Its public help page does not disclose an
accuracy, Macro-F1, category taxonomy, or a result on the FraudLens dataset.

This is an important practical comparison. Google Messages protects the inbox;
FraudLens helps a reviewer structure evidence after a suspicious message or
screenshot is available. FraudLens exposes an eight-class label, extracted
identifiers, risk reasons, a complaint draft, consent controls, and masked
cross-case relationships. Those features establish a broader documented
review workflow, not a claim that FraudLens detects spam more accurately.

## Phishing URL Detection

Phishing URL detection research shows that URL-only models can reach strong results when trained on large URL datasets.

The Scientific Reports 2024 study compared deterministic and probabilistic neural network models for phishing URL detection [9].

It found that uncertainty-aware probabilistic outputs improved accuracy by around 4 percent and helped explain uncertain URL predictions [9].

FraudLens Bharat uses simpler Phase 1 URL heuristics: non-HTTPS links, shorteners, IP hostnames, suspicious URL keywords, and hyphenated domains.

This is less powerful than a trained URL model but easier to audit and run locally during Phase 1.

## Graph-Based Fraud Detection

Graph Neural Networks are widely studied for financial fraud because fraud often depends on relationships among accounts, phone numbers, devices, URLs, and transactions.

Cheng et al. reviewed over 100 studies on GNNs for financial fraud detection and described their strength in modeling relational patterns [10].

The historical Phase 1 implementation stopped at entity extraction. The current
basic graph links repeated phone, UPI, email, and URL identifiers across
explicitly stored, unexpired cases using masked labels and opaque HMAC-backed
identifiers.

This observational view does not change classification or risk and does not
perform production fraud-network detection or use a GNN. More advanced graph
modeling remains a research direction rather than a current capability.

## Explainability And Trust

Ribeiro, Singh, and Guestrin argued that explanations are important when people need to decide whether to trust a classifier [11].

Their LIME work motivates a broader design principle: predictions should be paired with reasons that a user can inspect.

NIST's AI RMF also emphasizes trustworthy AI characteristics such as validity, reliability, accountability, transparency, explainability, privacy, and fairness [13].

FraudLens Bharat follows these principles through visible entities, risk signals, confidence, and a complaint draft. The current explanation method is rule-based rather than LIME-based. That is acceptable for Phase 1 because each score contribution is explicit.

## Baseline ML And Reproducibility

The current classifier uses scikit-learn's standard machine-learning stack through TF-IDF features and Logistic Regression.

Pedregosa et al. describe scikit-learn as a Python machine-learning library built for accessible supervised and unsupervised modeling [12].

This supports the Phase 1 choice: use a simple, reproducible baseline before moving to heavier transformer models.

## Research Gap Addressed By Phase 1

Most published systems focus on a single technical task such as classification, URL detection, or graph fraud modeling.

Phase 1 combined a small classifier, entity extraction, URL checks, risk scoring, local storage, FastAPI access, and a retired demonstration interface into one reproducible student prototype. The current final product uses the Next.js website and FastAPI.

The contribution is not state-of-the-art model performance. The contribution is an explainable end-to-end triage workflow for Indian Hinglish cyber-fraud messages.

## Sources

1. Ministry of Home Affairs, Press Information Bureau, "Assistance to States to Tackle Cyber Incidents," 24 March 2026. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2244504&lang=1&reg=3
2. National Cyber Crime Reporting Portal, Government of India. https://www.cybercrime.gov.in/
3. National Crime Records Bureau, Ministry of Home Affairs, "Crime in India Year Wise." https://www.ncrb.gov.in/crime-in-india-year-wise.html
4. Indian Computer Emergency Response Team, "Directions under sub-section (6) of section 70B of the Information Technology Act, 2000," 28 April 2022. https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf
5. Reserve Bank of India, "Master Direction on Digital Payment Security Controls," 18 February 2021. https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12032&Mode=0
6. National Payments Corporation of India, "Unified Payments Interface Product Overview." https://www.npci.org.in/what-we-do/upi/product-overview
7. N. Rani, D. Singh, B. Saha, and S. K. Shukla, "Automated Classification of Cybercrime Complaints using Transformer-based Language Models for Hinglish Texts," arXiv:2412.16614, 2024. https://arxiv.org/abs/2412.16614
8. R. Kapoor, Y. Kumar, K. Rajput, R. R. Shah, P. Kumaraguru, and R. Zimmermann, "Mind Your Language: Abuse and Offense Detection for Code-Switched Languages," arXiv:1809.08652, 2018. https://arxiv.org/abs/1809.08652
9. H. Ghalechyan et al., "Phishing URL detection with neural networks: an empirical study," Scientific Reports, 2024. https://www.nature.com/articles/s41598-024-74725-6
10. D. Cheng, Y. Zou, S. Xiang, and C. Jiang, "Graph Neural Networks for Financial Fraud Detection: A Review," arXiv:2411.05815, 2024. https://arxiv.org/abs/2411.05815
11. M. T. Ribeiro, S. Singh, and C. Guestrin, "'Why Should I Trust You?': Explaining the Predictions of Any Classifier," KDD, 2016. https://arxiv.org/abs/1602.04938
12. F. Pedregosa et al., "Scikit-learn: Machine Learning in Python," Journal of Machine Learning Research, 2011. https://jmlr.org/papers/v12/pedregosa11a.html
13. National Institute of Standards and Technology, "Artificial Intelligence Risk Management Framework (AI RMF 1.0)," NIST AI 100-1, 2023. https://doi.org/10.6028/NIST.AI.100-1
14. R. Nayak and R. Joshi, "L3Cube-HingCorpus and HingBERT: A Code Mixed Hindi-English Dataset and BERT Language Models," WILDRE-6, 2022. https://aclanthology.org/2022.wildre-1.2/
15. Google, "How Google protects your privacy with spam detection," Google Messages Help. https://support.google.com/messages/answer/9327903?hl=en. Accessed 11 August 2026.
