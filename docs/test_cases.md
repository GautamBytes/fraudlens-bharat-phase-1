# Phase 1 Test Cases

| Test Case ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-001 | Health endpoint | `GET /health` | API status is `ok` | Automated |
| TC-002 | KYC scam classification | Fake KYC message with urgent link | Fraud type `kyc_scam`, risk medium/high | Automated/manual |
| TC-003 | OTP phishing extraction | Message containing OTP and password request | OTP-like code and threat phrase extracted | Automated/manual |
| TC-004 | UPI refund scam extraction | Message containing UPI ID and refund wording | UPI entity and refund signal extracted | Automated/manual |
| TC-005 | URL risk shortener | Text containing `bit.ly` link | Shortened URL risk signal produced | Automated |
| TC-006 | URL risk non-HTTPS | Text containing `http://` URL | Non-HTTPS risk signal produced | Automated |
| TC-007 | Phone extraction | Text containing Indian mobile number | Phone entity extracted in normalized form | Automated |
| TC-008 | Money extraction | Text containing `Rs 1499` | Money entity extracted | Automated |
| TC-009 | Risk scoring low | Low confidence, no risky entities | Risk level `low` | Automated |
| TC-010 | Risk scoring high | High confidence, risky URL, urgency, OTP | Risk level `high` | Automated |
| TC-011 | Case storage | Analyze message via API | Case appears in `/cases` | Automated/manual |
| TC-012 | Dashboard demo | Click fake job demo button | Dashboard shows prediction, entities, explanation | Manual |

