# Weekly Progress Summary - Phase 1

| Week | Task Planned | Task Completed | Supervisor Remark |
|---|---|---|---|
| 1 | Finalize problem statement and project title | Drafted problem context around Hinglish cyber-fraud triage | Scope kept focused on triage, not a general chatbot |
| 2 | Literature review and reference collection | Collected NCRP/I4C, Hinglish classification, phishing, explainability references | Literature now mapped to Phase 1 modules |
| 3 | Define scope, architecture, and dataset policy | Created module plan, ethics policy, and Phase 1 acceptance criteria | Phase 2 items separated from Phase 1 |
| 4 | Prepare label taxonomy and dataset guide | Defined 8 fraud classes and labeling rules | Taxonomy documented in report and labeling guide |
| 5 | Build seed dataset | Created initial labelled synthetic dataset | Dataset remains synthetic and no-PII |
| 6 | Implement preprocessing and entity extraction | Added text cleanup and entity detection modules | Regression checks added for entity edge cases |
| 7 | Implement baseline ML model | Built TF-IDF + Logistic Regression training pipeline | Hybrid baseline compared with rule-only fallback |
| 8 | Implement URL/identifier risk scoring | Added rule-based URL and signal scoring | Risk signals kept explainable |
| 9 | Build FastAPI backend | Added health, analyze, cases endpoints | API covered by automated tests |
| 10 | Build Streamlit dashboard | Added message analysis UI and demo cases | Dashboard uses the same backend analysis path |
| 11 | Testing and validation | Added pytest suite and generated metrics | Current suite passes with 15 automated tests |
| 12 | Phase 1 report and demo preparation | Prepared report, screenshots checklist, demo outputs, and comparison docs | Final supervisor feedback pending after demo |
