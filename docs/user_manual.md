# User Manual

## Purpose

FraudLens Bharat helps a user analyze suspicious scam messages and prepare a structured report summary. It does not replace official reporting portals or law enforcement advice.

## Analyze a Message

1. Open the Streamlit dashboard.
2. Paste the suspicious SMS/WhatsApp text into the message box.
3. Leave **Store this analysis locally** unchecked unless you explicitly want a local SQLite history entry.
4. Click **Analyze Message**.
5. Review the predicted fraud type, risk level, confidence score, extracted entities, explanation, model version, abstention status, and storage status.

## Use Demo Messages

The dashboard includes demo buttons for:

- Fake KYC SMS
- OTP phishing
- Fake job scam
- Investment scam

Click a demo button, then analyze the loaded message.

## Analyze a Screenshot

1. Open the **Screenshot** tab.
2. Choose one PNG or JPEG screenshot.
3. Leave **Store this analysis locally** unchecked unless you consent to storing the extracted OCR text in local case history.
4. Click **Analyze Screenshot**.
5. Review the extracted text, fraud classification, risk evidence, and complaint draft.

Screenshot input supports PNG and JPEG files up to 5 MiB. The maximum width and
height are 4096 x 4096, and the decoded image may contain at most 16,000,000
pixels. OCR reads English and Hindi text (`eng+hin`). Animated, corrupt, or
unsupported images are rejected.

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
- `413`: the encoded image exceeds 5 MiB or decoded dimensions/pixels exceed the limits.
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
- **Storage status**: Confirms whether the analysis was saved. Storage is opt-in in the dashboard; a temporary storage failure leaves the analysis visible and reports that it was not stored.

## Safety Note

Replace real phone numbers, account numbers, UPI IDs, and names with dummy
values when testing. Review screenshots for private information before upload,
and enable local storage only with the affected person's consent.
