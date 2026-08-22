import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SignalField } from "@/components/signal-field";

const stylesheet = readFileSync(resolve(process.cwd(), "src/app/globals.css"), "utf8");

describe("hero signal motion", () => {
  it("renders three markers on one full orbit track", () => {
    const { container } = render(<SignalField />);

    expect(container.querySelector(".signalField")).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelectorAll(".signalNode")).toHaveLength(3);
    expect(container.querySelectorAll(".signalOrbitTrack")).toHaveLength(1);
    expect(container.querySelectorAll(".signalDepthArc")).toHaveLength(0);
  });

  it("defines the enlarged staggered evidence orbit", () => {
    expect(stylesheet).toContain("grid-template-columns:minmax(0,1.15fr) minmax(440px,.85fr)");
    expect(stylesheet).toContain("font-size:clamp(3.5rem,4.7vw,5.1rem)");
    expect(stylesheet).toContain("width:94%;height:78%");
    expect(stylesheet).toContain("offset-path:ellipse(47% 39% at 50% 42%)");
    expect(stylesheet).toContain("animation:signal-orbit 18s linear infinite");
    expect(stylesheet).toContain("animation-delay:-6s");
    expect(stylesheet).toContain("animation-delay:-12s");
    expect(stylesheet).toContain("@media(prefers-reduced-motion:reduce)");
    expect(stylesheet).toContain(".signalNode{display:none}");
    expect(stylesheet.includes("signal-depth-orbit")).toBe(false);
    expect(stylesheet.includes("perspective(900px)")).toBe(false);
  });
});
