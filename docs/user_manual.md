# User Manual

## Purpose

FraudLens Bharat helps a user analyze suspicious scam messages and prepare a structured report summary. It does not replace official reporting portals or law enforcement advice.

For the Docker release, open the Next.js website at `http://127.0.0.1:3000`.
An operator can check API liveness at `/health` and dependency readiness at
`/ready`; both responses identify release `1.0.0`. For API-only use, run
`uvicorn fraudlens.api:app --host 127.0.0.1 --port 8000`.

The landing page is public. Select **Professor sign in** and use the reviewer
email/password supplied by the project author before opening Analyze,
Relationships, Research, or Run guide. Public sign-up is disabled. Select
**Sign out** when the assessment is complete, especially on a shared machine.

## Analyze a Message

1. Open **Analyze** (`/analyze`) in the website and select the **Message text** tab.
2. Paste the suspicious SMS/WhatsApp text into the message box.
3. Leave **Store this synthetic analysis** unchecked unless you explicitly want a local SQLite history entry.
4. Click **Analyze message**.
5. Review the predicted fraud type, risk level, confidence score, extracted entities, explanation, model version, abstention status, and storage status.

## Use Demo Messages

The website includes demo buttons for:

- Fake KYC
- Courier hold
- Digital arrest
- Investment trap

Click a demo button, then analyze the loaded message.

## Analyze a Screenshot

1. Open **Analyze** (`/analyze`) and select the **Screenshot** tab.
2. Choose one PNG or JPEG screenshot.
3. Leave **Store this synthetic analysis** unchecked unless you consent to storing the extracted OCR text in local case history.
4. Click **Analyze screenshot**.
5. Review the extracted text, fraud classification, risk evidence, and complaint draft.

The website accepts PNG and JPEG screenshots up to 4,000,000 bytes (4 MB).
The backend API accepts up to 5 MiB, with maximum dimensions of 4096 x 4096 and
at most 16,000,000 decoded pixels. OCR reads English and Hindi text (`eng+hin`).
Animated, corrupt, or unsupported images are rejected.

Images are never retained. FraudLens normalizes each accepted image in memory
and sends it to the local Tesseract process. OCR text is stored only when you
explicitly enable local case storage. Stored OCR text follows the configured
retention period and the same deletion controls as pasted text.

## Analyze a Screenshot through the API

Send the image bytes as the request body. Do not use a multipart upload.

```bash
curl -X POST "http://127.0.0.1:8000/analyze-image?store_case=false" \
  -H "Content-Type: image/png" \
  --data-binary @screenshot.png
```

Use `Content-Type: image/jpeg` for JPEG files. Set the `store_case` query
parameter to `true` only after obtaining consent to retain the extracted text.

The screenshot endpoint uses generic error messages and does not return OCR
process details, file paths, or image-parser diagnostics:

- `400`: the `Content-Length` header is invalid.
- `413`: the website proxy rejects images over 4,000,000 bytes (4 MB); the API
  rejects images over 5 MiB or decoded dimensions/pixels over its limits.
- `415`: the media type or content encoding is unsupported.
- `422`: the image is invalid, contains no readable text, or OCR cannot analyze it.
- `503`: the local OCR service is unavailable.
- `504`: OCR exceeded its time limit.
- `500`: an unexpected internal error occurred.

## Read the Result

- **Fraud type**: The most likely category.
- **Risk level**: Low, medium, or high.
- **Extracted entities**: Phone numbers, URLs, UPI IDs, emails, amounts, OTP-like codes, and suspicious phrases.
- **Explanation**: Reasons behind the risk score.
- **Complaint draft**: A structured summary that can help the user manually prepare a report.
- **Storage status**: Confirms whether the analysis was saved. Storage is opt-in through **Store this synthetic analysis**; a temporary storage failure leaves the analysis visible and reports that it was not stored.

## Inspect Relationships

The **Relationships** (`/relationships`) page is an optional, observational view of repeated
evidence. It includes only explicitly stored, unexpired cases and supports
phone numbers, UPI IDs, email addresses, and URLs. It does not inspect analyses
that were not saved locally.

Choose a repeated-incident threshold from 2 through 20, then select Build
synthetic link or Refresh. The website does not run the graph query until
explicit Build synthetic link or Refresh. The API defaults for `GET /graph` are
`minimum_case_count=2` and `case_limit=100`.
minimum_case_count must be between 2 and 20, and case_limit must be between 1
and 100. The graph uses a fixed internal max_edges=1000 bound; it is not an API
query parameter.

API entity nodes expose opaque HMAC-backed identifiers and masked labels. The
website shows masked labels and hides opaque identifiers. Graph output does not
include raw text or raw entity values. If the graph is empty, no qualifying
stored cases meet the selected threshold. If it is marked `truncated`, the safe
display limit was reached; narrow the investigation or raise the threshold
before interpreting it.

Deleting a case, clearing case history, or retention expiry removes its graph
links. Graph results do not change a case's risk score or fraud classification.
This is not fraud-network detection, a production fraud-network claim, or a
GNN; it is a bounded visualization of locally retained evidence.

## Safety Note

Replace real phone numbers, account numbers, UPI IDs, and names with dummy
values when testing. Review screenshots for private information before upload,
and enable local storage only with the affected person's consent.

Application request logs contain a generated request ID, HTTP method, route
template, and status code only. They intentionally omit message text, OCR text,
notes, query strings, headers, client addresses, and concrete case IDs. The
response `X-Request-ID` can be used to correlate a request with that safe event.
