import { describe, expect, it } from "vitest";

describe("professor authentication policy", () => {
  it("keeps only the showcase, login, auth handler, and health endpoint public", async () => {
    const policy = await import("./auth-policy").catch(() => null);

    expect(policy).not.toBeNull();
    expect(policy?.requiresProfessorSession("/")).toBe(false);
    expect(policy?.requiresProfessorSession("/login")).toBe(false);
    expect(policy?.requiresProfessorSession("/api/auth/get-session")).toBe(false);
    expect(policy?.requiresProfessorSession("/api/health")).toBe(false);
    expect(policy?.requiresProfessorSession("/analyze")).toBe(true);
    expect(policy?.requiresProfessorSession("/relationships")).toBe(true);
    expect(policy?.requiresProfessorSession("/research")).toBe(true);
    expect(policy?.requiresProfessorSession("/guide")).toBe(true);
    expect(policy?.requiresProfessorSession("/api/analyze")).toBe(true);
    expect(policy?.requiresProfessorSession("/api/cases")).toBe(true);
    expect(policy?.requiresProfessorSession("/api/graph")).toBe(true);
  });

  it("allows only local application paths as post-login destinations", async () => {
    const policy = await import("./auth-policy").catch(() => null);

    expect(policy).not.toBeNull();
    expect(policy?.safeReturnPath("/analyze?tab=image")).toBe("/analyze?tab=image");
    expect(policy?.safeReturnPath("https://attacker.example")).toBe("/analyze");
    expect(policy?.safeReturnPath("//attacker.example")).toBe("/analyze");
    expect(policy?.safeReturnPath("/\\attacker.example")).toBe("/analyze");
    expect(policy?.safeReturnPath("/%2f%2fattacker.example")).toBe("/analyze");
    expect(policy?.safeReturnPath("/login")).toBe("/analyze");
    expect(policy?.safeReturnPath(null)).toBe("/analyze");
  });
});
