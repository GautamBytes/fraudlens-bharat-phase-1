import { describe, expect, it } from "vitest";

import { authConfigurationError } from "./auth-configuration";

describe("Better Auth environment validation", () => {
  it("fails closed when a production request lacks durable authentication configuration", () => {
    expect(authConfigurationError({ NODE_ENV: "production" })).toBe(
      "Authentication service is not configured",
    );
    expect(authConfigurationError({
      NODE_ENV: "production",
      DATABASE_URL: "postgresql://db.example/fraudlens",
      BETTER_AUTH_URL: "https://fraudlens-bharat.vercel.app",
      BETTER_AUTH_SECRET: "too-short",
    })).toBe("Authentication service is not configured");
    expect(authConfigurationError({
      NODE_ENV: "production",
      DATABASE_URL: "https://db.example/fraudlens",
      BETTER_AUTH_URL: "https://fraudlens-bharat.vercel.app",
      BETTER_AUTH_SECRET: "0123456789abcdef0123456789abcdef",
    })).toBe("Authentication service is not configured");
    expect(authConfigurationError({
      NODE_ENV: "production",
      DATABASE_URL: "postgresql://db.example/fraudlens",
      BETTER_AUTH_URL: "http://fraudlens-bharat.vercel.app",
      BETTER_AUTH_SECRET: "0123456789abcdef0123456789abcdef",
    })).toBe("Authentication service is not configured");
    expect(authConfigurationError({
      NODE_ENV: "production",
      DATABASE_URL: "postgresql://db.example/fraudlens",
      BETTER_AUTH_URL: "https://fraudlens-bharat.vercel.app",
      BETTER_AUTH_SECRET: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    })).toBe("Authentication service is not configured");
  });

  it("accepts strong production configuration and local development defaults", () => {
    expect(authConfigurationError({
      NODE_ENV: "production",
      DATABASE_URL: "postgresql://db.example/fraudlens",
      BETTER_AUTH_URL: "https://fraudlens-bharat.vercel.app",
      BETTER_AUTH_SECRET: "A7p!2mQ#9vL$4xR@8kT%6nW&3cY*5hJ?",
    })).toBeNull();
    expect(authConfigurationError({
      NODE_ENV: "production",
      DATABASE_URL: "postgresql://db.example/fraudlens",
      BETTER_AUTH_URL: "http://127.0.0.1:3000",
      BETTER_AUTH_SECRET: "A7p!2mQ#9vL$4xR@8kT%6nW&3cY*5hJ?",
    })).toBeNull();
    expect(authConfigurationError({ NODE_ENV: "development" })).toBeNull();
  });
});
