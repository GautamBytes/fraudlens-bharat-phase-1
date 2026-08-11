import { betterAuth } from "better-auth";
import { nextCookies } from "better-auth/next-js";
import { Pool } from "pg";

import {
  BUILD_ONLY_AUTH_SECRET,
  LOCAL_AUTH_BASE_URL,
  LOCAL_AUTH_DATABASE_URL,
} from "@/lib/auth-configuration";

function trustedOrigins(): string[] {
  const origins = new Set<string>([
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://fraudlens-bharat.vercel.app",
  ]);
  for (const value of [
    process.env.BETTER_AUTH_URL,
    process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : undefined,
  ]) {
    if (value) origins.add(value);
  }
  return [...origins];
}

export const authDatabase = new Pool({
  connectionString: process.env.DATABASE_URL ?? LOCAL_AUTH_DATABASE_URL,
  max: 3,
  idleTimeoutMillis: 20_000,
  connectionTimeoutMillis: 10_000,
});

export function createFraudLensAuth({ allowSignUp = false } = {}) {
  return betterAuth({
    appName: "FraudLens Bharat",
    baseURL: process.env.BETTER_AUTH_URL ?? LOCAL_AUTH_BASE_URL,
    secret: process.env.BETTER_AUTH_SECRET ?? BUILD_ONLY_AUTH_SECRET,
    database: authDatabase,
    trustedOrigins: trustedOrigins(),
    emailAndPassword: {
      enabled: true,
      disableSignUp: !allowSignUp,
      minPasswordLength: 12,
      maxPasswordLength: 128,
    },
    session: {
      expiresIn: 60 * 60 * 8,
      updateAge: 60 * 60,
      cookieCache: {
        enabled: true,
        maxAge: 60 * 5,
        strategy: "jwe",
      },
    },
    rateLimit: {
      enabled: true,
      storage: "database",
      window: 60,
      max: 60,
      customRules: {
        "/sign-in/email": { window: 60, max: 5 },
      },
    },
    advanced: {
      useSecureCookies: process.env.NODE_ENV === "production",
      defaultCookieAttributes: {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
      },
    },
    telemetry: { enabled: false },
    plugins: [nextCookies()],
  });
}

export const auth = createFraudLensAuth();
