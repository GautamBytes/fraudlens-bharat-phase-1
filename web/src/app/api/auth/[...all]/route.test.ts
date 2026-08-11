import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  configurationError: vi.fn(),
}));

vi.mock("better-auth/next-js", () => ({
  toNextJsHandler: () => ({ GET: mocks.get, POST: mocks.post }),
}));
vi.mock("@/lib/auth", () => ({ auth: {} }));
vi.mock("@/lib/auth-configuration", () => ({
  authConfigurationError: mocks.configurationError,
}));

describe("Better Auth route boundary", () => {
  beforeEach(() => {
    mocks.configurationError.mockReturnValue(null);
  });

  it("returns a fixed unavailable response when the authentication database fails", async () => {
    mocks.get.mockRejectedValue(new Error("postgresql://private-host/fraudlens"));
    const { GET } = await import("./route");

    const response = await GET(new Request("http://localhost/api/auth/get-session"));

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({ detail: "Authentication service is unavailable" });
    expect(response.headers.get("cache-control")).toBe("no-store");
  });

  it("fails closed before calling Better Auth when production configuration is missing", async () => {
    mocks.configurationError.mockReturnValue("Authentication service is not configured");
    const { POST } = await import("./route");

    const response = await POST(new Request("http://localhost/api/auth/sign-in/email", {
      method: "POST",
    }));

    expect(response.status).toBe(503);
    expect(mocks.post).not.toHaveBeenCalled();
  });
});
