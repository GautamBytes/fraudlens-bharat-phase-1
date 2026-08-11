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
| TC-012 | Website demo | In `/analyze`, select Fake KYC, Courier hold, Digital arrest, or Investment trap | Website shows prediction, entities, explanation | Manual |
| TC-013 | Email/UPI separation | Text containing `hr@jobpay.example` | Email extracted, no partial `hr@jobpay` UPI false positive | Automated |
| TC-014 | Contextual money extraction | Text containing `Invest 5000` and `2500 cashback` | Bare contextual amounts extracted as money | Automated |
| TC-015 | Hinglish FIR ambiguity | Text containing `fir bhi` in a loan context | No digital-arrest marker is added | Automated |
| TC-016 | Baseline training metrics | Run `python -m fraudlens.model_training` | Metrics JSON, report, and confusion matrix regenerated | Automated/manual |
| TC-017 | Screenshot OCR analysis | In `/analyze` > Screenshot, valid PNG/JPEG up to 4,000,000 bytes (4 MB) containing English or Hindi scam text | OCR text is analyzed and image-source metadata is returned | Automated/manual |
| TC-018 | Screenshot format rejection | WebP, GIF, mismatched media type, or multipart body | Input is rejected without starting OCR | Automated |
| TC-019 | Screenshot size rejection | Website image larger than 4,000,000 bytes (4 MB), or API image larger than 5 MiB | Website and API return generic `413` before OCR | Automated |
| TC-020 | Screenshot dimension and pixel rejection | Image over 4096 x 4096 or 16,000,000 pixels | Input is rejected by decompression and dimension guards | Automated |
| TC-021 | Screenshot retention consent | Analyze with **Store this synthetic analysis** off, then on | Image bytes are never retained; OCR text appears only in the opted-in case | Automated |
| TC-022 | OCR failure redaction | OCR unavailable, timeout, corrupt image, or internal OCR detail | API and website return fixed safe messages without process details | Automated |
| TC-023 | Screenshot metadata removal | PNG/JPEG containing EXIF, ICC, or text metadata | OCR receives a fresh metadata-free RGB PNG | Automated |
| TC-024 | OCR command boundary | Valid screenshot | Tesseract runs through stdin/stdout with `eng+hin`, fixed page segmentation, timeout, and no shell | Automated |
| TC-025 | Entity graph privacy contract | Repeated phone, UPI, email, and URL in explicitly stored cases | API exposes masked labels and HMAC-backed IDs only; website shows masks but hides IDs; no raw text or raw entity values | Automated/manual |
| TC-026 | Entity graph retention and deletion | Delete one stored case, clear history, or expire retained cases | Removed cases no longer contribute graph links | Automated |
| TC-027 | Entity graph API bounds and empty result | `GET /graph` defaults, out-of-range query values, and no qualifying cases | Safe defaults/bounds are enforced; empty graph is serialized without raw data | Automated |
| TC-028 | Entity graph website refresh and truncation | In `/relationships`, select Build synthetic link or Refresh and exceed a display limit | No graph query before an explicit button action; stale views are hidden and truncation is disclosed | Automated/manual |
| TC-029 | Release identity and readiness | Read OpenAPI, `GET /health`, and `GET /ready` | Package/API version is `1.0.0`; readiness checks storage and returns a generic `503` on failure | Automated |
| TC-030 | Privacy-safe request observability | Analyze sensitive text and request a concrete case path | Logs contain generated request ID, method, route template, and status only; sensitive request data is absent | Automated |
| TC-031 | Hardened container boundary | Build and inspect the production image | Pinned base and hashed runtime dependencies install; process is UID 10001; pip, setuptools, and pytest are absent; English/Hindi OCR is present | Automated |
| TC-032 | Production Compose policy | Validate and launch `compose.yaml` | Explicit strong secret/allowed hosts are required; ports bind to loopback; root filesystem is read-only and capabilities are dropped | Automated/manual |
| TC-033 | Full release acceptance journey | Analyze unconsented text, consented text/image, graph repeated evidence, delete, and clear | Consent, non-retention of image bytes, masking, retention storage, deletion, and readiness work together | Automated |
| TC-034 | CI container smoke gate | Run the `container-smoke` job | Image builds, restricted API becomes ready, model analyzes, OCR languages exist, dependencies check, and sensitive marker is absent from logs | Automated |
| TC-035 | Professor page authentication | Open Analyze, Relationships, Research, or Run guide without a session | Website redirects to Professor access and preserves a safe same-origin return path | Automated/manual |
| TC-036 | Protected API authentication | Call text analysis, screenshot analysis, relationship graph, or case reset without a valid session | Same-origin API returns generic `401` before contacting FastAPI | Automated |
| TC-037 | Reviewer sign-in and sign-out | Sign in with the provisioned professor account, then sign out | Protected workspace opens; sign-out clears the session and returns to the public landing page | Automated/manual |
| TC-038 | Authentication abuse and failure boundary | Repeated invalid sign-ins, malformed return URL, missing production configuration, or unavailable PostgreSQL | Database-backed rate limit applies; redirects stay same-origin; failures remain generic and fail closed | Automated/manual |
| TC-039 | Public sign-up boundary | Attempt to create an account through the Better Auth API or website | Public registration is unavailable; only the local provisioning command can create the reviewer | Automated/manual |
