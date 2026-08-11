import process from "node:process";

import { authDatabase, createFraudLensAuth } from "../src/lib/auth";

const email = process.env.FRAUDLENS_PROFESSOR_EMAIL?.trim().toLowerCase();
const password = process.env.FRAUDLENS_PROFESSOR_PASSWORD ?? "";
const name = process.env.FRAUDLENS_PROFESSOR_NAME?.trim() || "Professor Reviewer";

if (!email || !email.includes("@")) {
  throw new Error("Set FRAUDLENS_PROFESSOR_EMAIL to the reviewer email address");
}
if (password.length < 12 || password.length > 128) {
  throw new Error("FRAUDLENS_PROFESSOR_PASSWORD must contain 12 to 128 characters");
}

const provisioningAuth = createFraudLensAuth({ allowSignUp: true });

try {
  await provisioningAuth.api.signUpEmail({ body: { email, password, name } });
  console.info(`Created the FraudLens professor account for ${email}`);
} finally {
  await authDatabase.end();
}
