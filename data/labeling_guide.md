# FraudLens Bharat Phase 1 Labeling Guide

## Goal

Create a labelled text dataset for cyber-fraud triage in Hinglish, Hindi, and English. Every example must represent a possible scam message or complaint text and be assigned exactly one primary label.

## Labels

| Label | Meaning | Common Signals |
|---|---|---|
| `kyc_scam` | Fake KYC/update/verification messages impersonating banks, wallets, telecom, or government identity systems | KYC blocked, account freeze, PAN/Aadhaar update, verify now, urgent link |
| `digital_arrest` | Threat-based impersonation of police, customs, CBI, court, cyber cell, or courier crime investigation | arrest warrant, money laundering, parcel seized, video call, do not tell anyone |
| `fake_job` | Fake work-from-home, part-time, placement, HR, registration fee, task earning, or interview scam | salary promise, registration fee, daily earning, joining kit, Telegram HR |
| `investment_scam` | Fake trading, crypto, stock tips, doubling money, guaranteed profit, VIP group scams | guaranteed return, double money, crypto, trading signal, investment plan |
| `loan_scam` | Fake instant loan, low-interest loan, processing fee, loan approval, threat of legal action | instant loan, processing fee, CIBIL, foreclosure, penalty threat |
| `courier_scam` | Fake courier/customs/FedEx/DHL/parcel crime messages | parcel blocked, customs, drugs, passport, courier verification |
| `upi_refund_scam` | Fake cashback/refund/payment receive requests that trick users into entering UPI PIN | refund, cashback, receive money, collect request, enter UPI PIN |
| `otp_phishing` | OTP/password/login credential stealing or account takeover attempts | OTP, password, login, PIN, CVV, verification code |

## Labeling Rules

- Use the most specific label based on the main intent.
- If a message includes a link and asks for OTP, use `otp_phishing`.
- If the message focuses on KYC/account blockage, use `kyc_scam`.
- If it uses police/customs/court threats, use `digital_arrest` or `courier_scam` depending on the main story.
- Do not include real victim names, real phone numbers, real UPI IDs, or private screenshots in Phase 1.
- Synthetic examples should include realistic Hinglish, short forms, misspellings, urgency, and imperfect grammar.

## Quality Checklist

- The label is unambiguous.
- The text contains enough evidence for a classifier to learn from it.
- The example does not expose private data.
- Hinglish examples should not sound overly formal.

