import { beforeEach, describe, expect, it, vi } from "vitest";

import { auth } from "@/lib/auth";
import { authConfigurationError } from "@/lib/auth-configuration";
import { requireProfessorSession } from "./authorization";

vi.mock("@/lib/auth", () => ({
  auth: { api: { getSession: vi.fn() } },
}));
vi.mock("@/lib/auth-configuration", () => ({ authConfigurationError: vi.fn() }));

describe("requireProfessorSession", () => {
  beforeEach(() => {
    vi.mocked(authConfigurationError).mockReturnValue(null);
  });

  it("returns a generic unauthorized response without a session", async () => {
    vi.mocked(auth.api.getSession).mockResolvedValue(null);

    const response = await requireProfessorSession(new Request("http://localhost/api/analyze"));

    expect(response?.status).toBe(401);
    expect(await response?.json()).toEqual({ detail: "Professor authentication required" });
  });

  it("fails closed with a generic response when session storage is unavailable", async () => {
    vi.mocked(auth.api.getSession).mockRejectedValue(new Error("database details must stay private"));

    const response = await requireProfessorSession(new Request("http://localhost/api/analyze"));

    expect(response?.status).toBe(503);
    expect(await response?.json()).toEqual({ detail: "Authentication service is unavailable" });
  });
});
