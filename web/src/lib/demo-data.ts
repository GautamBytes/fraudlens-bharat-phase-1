export const DEMO_MESSAGES = [
  {
    label: "Fake KYC",
    text: "Your KYC expires today. Verify now at https://fraud-demo.example/kyc or your account will be blocked.",
  },
  {
    label: "Courier hold",
    text: "Courier parcel is held. Pay the release fee at https://fraud-demo.example/release immediately.",
  },
  {
    label: "Digital arrest",
    text: "Police case registered on your Aadhaar. Stay on this call and transfer verification money now.",
  },
  {
    label: "Investment trap",
    text: "Guaranteed 5x return today. Join our private investment group and send the first payment now.",
  },
] as const;

export const DEFAULT_DEMO_MESSAGE = DEMO_MESSAGES[0].text;
