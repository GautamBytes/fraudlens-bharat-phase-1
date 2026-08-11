import { NextRequest } from "next/server";
import { describe, expect, it, vi } from "vitest";

const { getCookieCache } = vi.hoisted(() => ({ getCookieCache: vi.fn() }));

vi.mock("better-auth/cookies", () => ({ getCookieCache }));

describe("professor page proxy", () => {
  it("redirects an unauthenticated protected page to login with a safe return path", async () => {
    const implementation = await import("./proxy").catch(() => null);
    expect(implementation).not.toBeNull();
    if (!implementation) return;
    getCookieCache.mockResolvedValue(null);

    const response = await implementation.proxy(new NextRequest("https://fraudlens-bharat.vercel.app/relationships?minimum=2"));

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(
      "https://fraudlens-bharat.vercel.app/login?returnTo=%2Frelationships%3Fminimum%3D2",
    );
  });

  it("allows a protected page through only with a cryptographically verified session cache", async () => {
    const implementation = await import("./proxy").catch(() => null);
    expect(implementation).not.toBeNull();
    if (!implementation) return;
    getCookieCache.mockResolvedValue({
      session: { id: "session", expiresAt: new Date(Date.now() + 60_000) },
      user: { id: "professor", email: "professor@example.edu" },
      updatedAt: Date.now(),
    });

    const response = await implementation.proxy(new NextRequest("https://fraudlens-bharat.vercel.app/analyze"));

    expect(response.status).toBe(200);
  });

  it("rejects a forged session token without a valid signed session cache", async () => {
    const implementation = await import("./proxy");
    getCookieCache.mockResolvedValue(null);
    const request = new NextRequest("https://fraudlens-bharat.vercel.app/research", {
      headers: { cookie: "better-auth.session_token=forged" },
    });

    const response = await implementation.proxy(request);

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toContain("/login?returnTo=%2Fresearch");
  });
});
