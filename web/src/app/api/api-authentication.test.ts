import { beforeEach, describe, expect, it, vi } from "vitest";

import { fraudlensRequest } from "@/lib/server/fraudlens";
import { requireProfessorSession } from "@/lib/server/authorization";
import { POST as analyzeText } from "./analyze/route";
import { POST as analyzeImage } from "./analyze-image/route";
import { DELETE as clearCases } from "./cases/route";
import { GET as readGraph } from "./graph/route";

vi.mock("@/lib/server/fraudlens", () => ({ fraudlensRequest: vi.fn() }));
vi.mock("@/lib/server/authorization", () => ({ requireProfessorSession: vi.fn() }));

describe("professor API boundary", () => {
  beforeEach(() => {
    vi.mocked(requireProfessorSession).mockImplementation(async () => Response.json(
      { detail: "Professor authentication required" },
      { status: 401 },
    ));
    vi.mocked(fraudlensRequest).mockResolvedValue(Response.json({ status: "unexpected" }));
  });

  it.each([
    ["text analysis", () => analyzeText(new Request("http://localhost/api/analyze", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: "synthetic KYC warning", store_case: false }),
    }))],
    ["image analysis", () => analyzeImage(new Request("http://localhost/api/analyze-image", {
      method: "POST",
      headers: { "content-type": "image/png" },
      body: new Uint8Array([1]),
    }))],
    ["case reset", () => clearCases(new Request("http://localhost/api/cases", { method: "DELETE" }))],
    ["relationship graph", () => readGraph(new Request("http://localhost/api/graph"))],
  ])("rejects unauthenticated %s before contacting the analysis backend", async (_name, call) => {
    const response = await call();

    expect(response.status).toBe(401);
    expect(await response.json()).toEqual({ detail: "Professor authentication required" });
    expect(fraudlensRequest).not.toHaveBeenCalled();
  });
});
