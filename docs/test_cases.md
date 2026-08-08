# FraudLens Bharat Test Cases

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
| TC-013 | Email/UPI separation | Text containing `hr@jobpay.example` | Email extracted, no partial `hr@jobpay` UPI false positive | Automated |
| TC-014 | Contextual money extraction | Text containing `Invest 5000` and `2500 cashback` | Bare contextual amounts extracted as money | Automated |
| TC-015 | Hinglish FIR ambiguity | Text containing `fir bhi` in a loan context | No digital-arrest marker is added | Automated |
| TC-016 | Baseline training metrics | Run `python -m fraudlens.model_training` | Metrics JSON, report, and confusion matrix regenerated | Automated/manual |
| TC-017 | Screenshot OCR analysis | Valid PNG containing English or Hindi scam text | OCR text is analyzed and image-source metadata is returned | Automated/manual |
| TC-018 | Screenshot format rejection | WebP, GIF, mismatched media type, or multipart body | Input is rejected without starting OCR | Automated |
| TC-019 | Screenshot size rejection | Encoded image larger than 5 MiB | API returns generic `413`; dashboard rejects before reading upload bytes | Automated |
| TC-020 | Screenshot dimension and pixel rejection | Image over 4096 x 4096 or 16,000,000 pixels | Input is rejected by decompression and dimension guards | Automated |
| TC-021 | Screenshot retention consent | Analyze with storage off, then with explicit storage on | Image bytes are never retained; OCR text appears only in the opted-in case | Automated |
| TC-022 | OCR failure redaction | OCR unavailable, timeout, corrupt image, or internal OCR detail | API and dashboard return fixed safe messages without process details | Automated |
| TC-023 | Screenshot metadata removal | PNG/JPEG containing EXIF, ICC, or text metadata | OCR receives a fresh metadata-free RGB PNG | Automated |
| TC-024 | OCR command boundary | Valid screenshot | Tesseract runs through stdin/stdout with `eng+hin`, fixed page segmentation, timeout, and no shell | Automated |
