import { beforeEach, describe, expect, it, vi } from "vitest";

import { fraudlensRequest } from "@/lib/server/fraudlens";
import { POST } from "./route";

vi.mock("@/lib/server/fraudlens", () => ({ fraudlensRequest: vi.fn() }));

describe("screenshot proxy", () => {
  beforeEach(() => {
    vi.mocked(fraudlensRequest).mockResolvedValue(
      Response.json({ predicted_label: "kyc_scam" }),
    );
  });

  it("rejects unsupported media before contacting the backend", async () => {
    const request = new Request("http://localhost/api/analyze-image", {
      method: "POST",
      headers: { "content-type": "image/gif" },
      body: new Uint8Array([1]),
    });

    const response = await POST(request);

    expect(response.status).toBe(415);
    expect(fraudlensRequest).not.toHaveBeenCalled();
  });

  it("rejects image bodies above 4,000,000 bytes before contacting the backend", async () => {
    const request = new Request("http://localhost/api/analyze-image", {
      method: "POST",
      headers: { "content-type": "image/png", "content-length": "4000001" },
      body: new Uint8Array([1]),
    });

    const response = await POST(request);

    expect(response.status).toBe(413);
    expect(fraudlensRequest).not.toHaveBeenCalled();
  });

  it("forwards a bounded PNG with an explicit storage choice", async () => {
    const request = new Request(
      "http://localhost/api/analyze-image?store_case=false",
      {
        method: "POST",
        headers: { "content-type": "image/png" },
        body: new Uint8Array([1, 2, 3]),
      },
    );

    const response = await POST(request);

    expect(response.status).toBe(200);
    expect(fraudlensRequest).toHaveBeenCalledWith(
      "/analyze-image?store_case=false",
      expect.objectContaining({
        method: "POST",
        headers: { "content-type": "image/png" },
        body: expect.any(ArrayBuffer),
      }),
      65_000,
    );
  });
});
