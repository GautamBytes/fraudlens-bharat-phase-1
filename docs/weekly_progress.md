# Weekly Progress Summary - Phase 1 + Phase 2

This is a student-maintained execution log. It records project evidence and
does not represent supervisor feedback; recorded and pending supervisor reviews
are listed separately in `docs/supervisor_interaction.md`.

> Current-scope note (2026-08-10): Phase 1 used a Streamlit demonstration interface. That interface is retired; the supported final product uses the Next.js website and FastAPI.

| Week | Task Planned | Task Completed | Project evidence / status |
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
| 11 | Testing and validation | Added pytest suite and generated metrics | Phase 1 test evidence recorded |
| 12 | Phase 1 report and demo preparation | Prepared report, screenshots checklist, demo outputs, and comparison docs | Phase 1 review package completed |
| 13 | Phase 2 evaluation design | Froze train, validation, and test roles; added abstention-aware metrics | Synthetic evidence boundary made explicit |
| 14 | Calibrated model and artifact trust | Added calibrated inference, provenance, hashes, and reproducible artifact checks | Runtime and research candidates kept separate |
| 15 | Screenshot OCR | Added bounded PNG/JPEG input and local Tesseract `eng+hin` analysis | Image bytes are not retained |
| 16 | OCR/API/interface integration | Routed screenshot text through the shared analysis service | Storage remains consent-gated |
| 17 | Entity relationship design | Added repeated phone, UPI, email, and URL-host links | Raw entity values excluded from relationship storage |
| 18 | Graph API and interface | Added bounded graph reads and explicit refresh | Graph documented as observational, not GNN detection |
| 19 | Privacy and retention hardening | Added HMAC identifiers, masks, expiry migration, and purge rules | Malformed retention rows fail closed |
| 20 | Release hardening | Added pinned locks, readiness, safe logs, and a non-root read-only container | Local release boundary documented |
| 21 | Research benchmark | Compared rules, word, character, hybrid, and calibrated candidates on one split | Character TF-IDF produced the best parsimonious result |
| 22 | Robustness and statistical analysis | Added deterministic perturbations and paired bootstrap | Results limited to the eight-row synthetic test |
| 23 | Final demo evidence | Regenerated named demos, current screenshots, architecture, and charts | Stale Phase 1 claims removed from final evidence |
| 24 | Final capstone package | Prepared final report, 10-slide deck, and video runbook | Full suite passes with 379 automated tests |
