# FraudLens Bharat Phase 1 - Pitch Script

Target duration: 8-10 minutes. Keep the tone practical: this is a progress-review pitch for a 6-month capstone, not a final product launch.

## Slide 1 - Title

Good morning sir. My project is FraudLens Bharat, an AI-based Hinglish cyber-fraud detection and complaint triage prototype. Phase 1 focuses on the stable software baseline: a user pastes a suspicious message, and the system classifies the scam type, extracts evidence, scores risk, and generates a complaint-ready summary. The implementation is already runnable through both FastAPI and Streamlit, with the code and evidence available in the GitHub repo.

## Slide 2 - Problem

The problem I am targeting is the gap between how cyber-fraud actually appears to users and how formal complaints need to be written. Indian scam messages are often in Hinglish or mixed Hindi-English, with slang, urgency, links, phone numbers, UPI IDs, and sometimes threats. A normal user may not know which details matter, so the system tries to convert messy input into structured evidence.

## Slide 3 - Research Grounding

This is not just a random classifier project. The project is backed by NCRP/I4C cyber-fraud reporting context, research on Hinglish cybercrime classification, phishing URL detection, and explainable AI. The research question for Phase 1 is whether a lightweight and explainable pipeline can classify common Indian cyber-fraud messages and extract useful complaint evidence from mixed-language text.

## Slide 4 - Architecture

The architecture is designed as a complete end-to-end loop. The input goes through preprocessing, then three parallel signal layers: baseline ML classification, entity extraction, and URL risk heuristics. These signals are combined by the risk-scoring module, stored in SQLite, and exposed through both the FastAPI backend and Streamlit dashboard.

## Slide 5 - Implemented Scope

Phase 1 includes more than the dashboard. I have implemented the dataset scaffold, an eight-label taxonomy, training and inference modules, entity extraction, risk scoring, API endpoints, dashboard, test cases, demo outputs, metrics, and documentation. The commands shown here are enough to train the model, run the API, run the dashboard, and execute the test suite.

## Slide 6 - Demo Proof

This slide shows the actual dashboard result. The user can paste scam text or use demo buttons, and the system returns the predicted scam type, confidence, risk level, extracted entities, explanation reasons, and a complaint-ready draft. The important point is that the demo is not manually staged; it calls the same backend pipeline used by the API.

## Slide 7 - Baseline Results

The baseline model uses TF-IDF with Logistic Regression. On the seed evaluation split, it currently gives 0.875 accuracy and 0.875 macro-F1. Most classes perform well in this small seed setup, while courier scam and digital arrest show overlap, which is useful because it gives a clear Phase 2 improvement target.

## Slide 8 - Testing Evidence

The project includes pytest coverage for preprocessing, entity extraction, URL risk, risk scoring, and the API flow. The API health endpoint and test screenshots are included as evidence, and the generated artifacts include metrics JSON, classification report, confusion matrix, and demo-case JSON outputs. This makes Phase 1 reproducible for review.

## Slide 9 - Controls And Limitations

I have intentionally kept ethical and technical boundaries clear. The dataset is synthetic for education, real victim PII is not required, and the system does not submit anything to a government portal automatically. The current limitations are also clear: small seed dataset, no OCR yet, no transformer fine-tuning yet, and no graph analytics in Phase 1.

## Slide 10 - Phase 2 Roadmap

For Phase 2, I plan to extend the system in four directions: OCR for screenshots, transformer comparison for Hinglish classification, graph analytics for repeated identifiers, and final hardening with a larger dataset and stronger evaluation. My request for feedback is whether this Phase 2 scope and the current Phase 1 evidence are aligned with the capstone expectations.

## Short Closing Line

In one sentence, FraudLens Bharat is a pure-software capstone that converts unstructured Indian cyber-fraud messages into classified, explainable, complaint-ready evidence.
