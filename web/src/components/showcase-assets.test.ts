import { existsSync, readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const SHOWCASE_ASSETS = [
  "text-analysis.png",
  "screenshot-analysis.png",
  "relationship-graph.png",
];

describe("recorded showcase assets", () => {
  it.each(SHOWCASE_ASSETS)("commits a substantive %s capture", (name) => {
    const path = resolve(process.cwd(), "public", "showcase", name);

    expect(existsSync(path)).toBe(true);
    expect(statSync(path).size).toBeGreaterThan(10_000);
  });

  it("captures an actual synthetic message image and masks recorded entities", () => {
    const script = readFileSync(resolve(process.cwd(), "scripts", "capture-showcase.mjs"), "utf8");

    expect(script).toContain("renderSyntheticMessage");
    expect(script).not.toContain("iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB");
    expect(script).toContain("fraud-demo[.]example/•••");
  });

  it("stacks page toolbars at the 768 pixel boundary", () => {
    const styles = readFileSync(resolve(process.cwd(), "src", "app", "globals.css"), "utf8");

    expect(styles).toContain("@media (max-width: 768px)");
  });
});
