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

  it("defines the enlarged staggered flat ellipse", () => {
    expect(stylesheet.includes("width: 84%; height: 72%")).toBe(true);
    expect(stylesheet.includes("offset-path: ellipse(42% 36% at 50% 38%)")).toBe(true);
    expect(stylesheet.includes("animation: signal-orbit 11s linear infinite")).toBe(true);
    expect(stylesheet.includes("animation-delay: -3.667s")).toBe(true);
    expect(stylesheet.includes("animation-delay: -7.333s")).toBe(true);
    expect(stylesheet.includes("animation: none !important")).toBe(true);
    expect(stylesheet.includes("signal-depth-orbit")).toBe(false);
    expect(stylesheet.includes("perspective(900px)")).toBe(false);
  });
});
