# FraudLens Bharat Demo Video Runbook

Use this runbook for the final 3 to 4 minute product recording and as a fallback
during the live meeting.

## Recording principles

- Use only the committed synthetic demo messages and screenshot.
- Keep storage off for normal analysis; the relationship step uses its own
  controlled synthetic seed action.
- Do not show terminals containing secrets, local paths, browser history, or
  notifications.
- Do not claim that a prediction proves fraud or that the system files a case.
- Record at 1920 x 1080 or higher with browser zoom at 100%.
- Keep the cursor still while explaining a result.

## Preflight

1. Check out the final merged commit and install the locked contributor
   environment.
2. Install Tesseract English and Hindi language data for a direct local demo.
3. Set a unique local `FRAUDLENS_HMAC_SECRET` without displaying it.
4. The graph action resets and seeds its own synthetic cases; no manual case
   history preparation is required.
5. Start the FastAPI service and Next.js website on loopback only.
6. Verify `GET /ready`, the website home, and the OCR language list.
7. Disable desktop notifications and close unrelated applications.
8. Open these evidence fallbacks in separate tabs:
   - `outputs/screenshots/final_text_analysis.png`
   - `outputs/screenshots/final_ocr_analysis.png`
   - `outputs/screenshots/final_entity_graph.png`
   - `outputs/screenshots/final_api_ready.png`
   - `outputs/screenshots/final_api_docs.png`

## Recording sequence

### 0:00-0:15 - Title and safe default

Show the Next.js website home page. Say: “FraudLens Bharat accepts pasted messages or
bounded screenshots. Local case storage starts off.” Then navigate to
`/analyze`; the home page has no storage control.

### 0:15-1:05 - Text analysis

1. Open **Analyze** (`/analyze`) and keep the **Message text** tab selected.
2. Confirm **Store this synthetic analysis** is unchecked, then load the named
   **Fake KYC** synthetic demo.
3. Click **Analyze message**.
4. Point to the scam category, confidence, risk band, extracted evidence,
   reasons, and complaint draft.
5. Say that the website and API use the same analysis service.

Expected evidence: the named demo produces its advertised category and a
non-abstained result. Do not quote a different confidence from memory; read the
current screen.

### 1:05-2:00 - Screenshot OCR

1. Select the **Screenshot** tab in **Analyze**.
2. Upload the committed synthetic PNG fixture, which must remain at or below
   4,000,000 bytes (4 MB) for the website.
3. Click **Analyze screenshot**.
4. Show the extracted text and the analysis result.
5. Point to the source and retention metadata.

Say: “The service validates PNG or JPEG policy, invokes local Tesseract with
English and Hindi, analyzes the extracted text, and does not retain image
bytes.”

Fallback: show `outputs/screenshots/final_ocr_analysis.png`. Never replace this
with a real victim screenshot.

### 2:00-3:05 - Consented repeated-entity graph

1. Open **Relationships** (`/relationships`) and keep the minimum case count at 2.
2. Click **Build synthetic link**. It clears earlier synthetic cases and seeds the synthetic KYC and courier cases that share `fraud-demo.example`, then loads the graph.
3. Point to the two incidents and the masked shared host. Use **Refresh** only
   when rerunning the graph read.

Say: “The graph reads only unexpired cases that I chose to retain. It uses
opaque HMAC identifiers and masked labels. It does not change a prediction and
is not a GNN fraud detector.”

Fallback: show `outputs/screenshots/final_entity_graph.png`.

### 3:05-3:35 - API and close

Show `GET /ready` and the Swagger page. State that FastAPI provides the same
analysis workflow and that the release has 358 automated tests plus Python
3.10, 3.11.15, 3.12, and container smoke checks.

Close with: “This is an assistive local prototype with human review, not a
production fraud verdict or automatic filing system.”

## Failure-safe fallback

If the website, OCR executable, or graph state fails during the meeting:

1. Stop clicking after the first failure; do not debug live.
2. State the failed boundary in one sentence, such as “The local OCR process is
   unavailable on this machine.”
3. Switch to the corresponding committed screenshot.
4. Show the API readiness screenshot and the relevant automated-test evidence.
5. Continue the recording without changing any result or metric.

The screenshot fallback is valid because PR 1 captured the final application
with synthetic fixtures and checked the same paths in the full suite and
container smoke test.

## Editing checklist

- Trim setup, loading pauses, and failed takes.
- Keep the video between 3:00 and 4:00.
- Add small section labels only: Analyze, OCR, Relationships, API.
- Do not add an accuracy animation or “AI detects fraud” claim.
- Blur any accidental secret, notification, local username, or unrelated tab.
- Use captions for the final narration and verify technical terms manually.
- Export H.264 MP4 at 1080p and watch the exported file once at normal speed.

## Evidence retention after recording

Keep the MP4 outside Git if it exceeds repository policy. Record its final
filename, duration, SHA-256 hash, and approved sharing location in the meeting
submission form. Do not commit real victim data or private meeting links.
