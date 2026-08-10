import { afterEach, describe, expect, it, vi } from "vitest";

import { fraudlensRequest } from "./fraudlens";

describe("fraudlensRequest", () => {
  afterEach(() => {
    delete process.env.FRAUDLENS_API_URL;
    delete process.env.FRAUDLENS_DEMO_API_KEY;
  });

  it("returns a generic unavailable response when the backend is not configured", async () => {
    const response = await fraudlensRequest("/health");

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({
      detail: "Analysis service is not configured",
    });
  });

  it("adds the server-only demo key and disables caching", async () => {
    process.env.FRAUDLENS_API_URL = "https://api.example.test/base/";
    process.env.FRAUDLENS_DEMO_API_KEY = "server-secret";
    const upstream = new Response(JSON.stringify({ status: "ok" }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
    const fetchMock = vi.fn().mockResolvedValue(upstream);
    vi.stubGlobal("fetch", fetchMock);

    const response = await fraudlensRequest("/health");

    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.test/health",
      expect.objectContaining({
        cache: "no-store",
        headers: expect.any(Headers),
      }),
    );
    const requestHeaders = fetchMock.mock.calls[0][1].headers as Headers;
    expect(requestHeaders.get("X-FraudLens-Demo-Key")).toBe("server-secret");
    expect(response.headers.get("cache-control")).toBe("no-store");
  });

  it("maps an upstream timeout to a generic 504 response", async () => {
    process.env.FRAUDLENS_API_URL = "https://api.example.test";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new DOMException("timeout", "TimeoutError")));

    const response = await fraudlensRequest("/ready");

    expect(response.status).toBe(504);
    await expect(response.json()).resolves.toEqual({
      detail: "Analysis service is still starting",
    });
  });
});
