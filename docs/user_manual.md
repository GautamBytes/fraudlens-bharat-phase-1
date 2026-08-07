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

## Read the Result

- **Fraud type**: The most likely category.
- **Risk level**: Low, medium, or high.
- **Extracted entities**: Phone numbers, URLs, UPI IDs, emails, amounts, OTP-like codes, and suspicious phrases.
- **Explanation**: Reasons behind the risk score.
- **Complaint draft**: A structured summary that can help the user manually prepare a report.
- **Storage status**: Confirms whether the analysis was saved. Storage is opt-in in the dashboard; a temporary storage failure leaves the analysis visible and reports that it was not stored.

## Safety Note

Do not upload or store real private victim information in Phase 1. Replace real phone numbers, account numbers, UPI IDs, and names with dummy values before testing.
