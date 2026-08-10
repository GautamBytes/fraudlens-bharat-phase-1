"""Synthetic, presentation-safe demo messages with explicit expected labels."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoCase:
    slug: str
    button_label: str
    expected_label: str
    text: str


DEMO_CASES = (
    DemoCase(
        slug="fake_kyc_sms",
        button_label="Fake KYC SMS",
        expected_label="kyc_scam",
        text=(
            "Dear customer your bank KYC is expired. Update PAN at "
            "http://bank-kyc-verify.example/login or account will block today."
        ),
    ),
    DemoCase(
        slug="otp_phishing",
        button_label="OTP Phishing",
        expected_label="otp_phishing",
        text=(
            "Security alert: email login blocked. Reply with OTP and password "
            "to prove ownership."
        ),
    ),
    DemoCase(
        slug="fake_job_scam",
        button_label="Fake Job Scam",
        expected_label="fake_job",
        text=(
            "Work from home job hai, salary 45000 monthly. Joining kit fee "
            "Rs 999 send karo to hr@jobpay.example."
        ),
    ),
    DemoCase(
        slug="investment_scam",
        button_label="Investment Scam",
        expected_label="investment_scam",
        text=(
            "Join crypto VIP group. Guaranteed 15 percent profit daily. "
            "Invest 5000 now and double in 7 days."
        ),
    ),
)
