type AuthEnvironment = Partial<
  Pick<
    NodeJS.ProcessEnv,
    "NODE_ENV" | "DATABASE_URL" | "BETTER_AUTH_URL" | "BETTER_AUTH_SECRET"
  >
>;

export const LOCAL_AUTH_DATABASE_URL =
  "postgresql://fraudlens:fraudlens@127.0.0.1:5432/fraudlens_auth";
export const LOCAL_AUTH_BASE_URL = "http://127.0.0.1:3000";
export const BUILD_ONLY_AUTH_SECRET =
  "fraudlens-local-build-secret-never-valid-for-production";

function hasExpectedProtocol(value: string, protocols: readonly string[]): boolean {
  try {
    return protocols.includes(new URL(value).protocol);
  } catch {
    return false;
  }
}

function isSecureOrLoopbackOrigin(value: string): boolean {
  try {
    const url = new URL(value);
    if (url.protocol === "https:") return true;
    return url.protocol === "http:"
      && ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname);
  } catch {
    return false;
  }
}

function isStrongSecret(value: string | undefined): boolean {
  if (!value || value.length < 32) return false;
  return new Set(value).size >= 12;
}

export function authConfigurationError(env: AuthEnvironment = process.env): string | null {
  if (env.NODE_ENV !== "production") return null;
  if (
    !env.DATABASE_URL
    || !hasExpectedProtocol(env.DATABASE_URL, ["postgres:", "postgresql:"])
    || !env.BETTER_AUTH_URL
    || !isSecureOrLoopbackOrigin(env.BETTER_AUTH_URL)
    || !isStrongSecret(env.BETTER_AUTH_SECRET)
  ) {
    return "Authentication service is not configured";
  }
  return null;
}
