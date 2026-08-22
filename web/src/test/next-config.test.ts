import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

async function loadConfig(vercel: string | undefined) {
  vi.resetModules();
  if (vercel === undefined) delete process.env.VERCEL;
  else process.env.VERCEL = vercel;
  return (await import("../../next.config")).default;
}

describe("Next.js deployment output", () => {
  afterEach(() => {
    delete process.env.VERCEL;
    vi.resetModules();
  });

  it("uses Vercel native output tracing during a Vercel build", async () => {
    expect((await loadConfig("1")).output).toBeUndefined();
  });

  it("keeps standalone output for the Docker image", async () => {
    expect((await loadConfig(undefined)).output).toBe("standalone");
  });

  it("keeps production builds independent from remote font downloads", () => {
    const layout = readFileSync(resolve(process.cwd(), "src/app/layout.tsx"), "utf8");

    expect(layout).not.toContain("next/font/google");
  });
});
