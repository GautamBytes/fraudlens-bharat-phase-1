import json

from fraudlens.api import analyze_message
from fraudlens.config import DEMO_CASES_DIR


DEMO_CASES = {
    "fake_kyc_sms": "Dear customer your bank KYC is expired. Update PAN at http://bank-kyc-verify.example/login or account will block today.",
    "otp_phishing": "Login attempt detected. Send OTP code 482913 to verify ur identity or account delete ho jayega.",
    "fake_job_scam": "Work from home job hai, salary 45000 monthly. Joining kit fee Rs 999 send karo to hr@jobpay.example.",
    "investment_scam": "Join crypto VIP group. Guaranteed 15 percent profit daily. Invest 5000 now and double in 7 days.",
}


def _dump(result):
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return json.loads(result.json())


def main() -> None:
    DEMO_CASES_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in DEMO_CASES.items():
        result = analyze_message(text)
        (DEMO_CASES_DIR / f"{name}.json").write_text(json.dumps(_dump(result), indent=2), encoding="utf-8")
        print(f"wrote {name}.json")


if __name__ == "__main__":
    main()

