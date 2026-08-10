import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RecordedDemoTour } from "./recorded-demo-tour";

describe("RecordedDemoTour", () => {
  it("shows three honest recorded demonstrations with direct routes", () => {
    render(<RecordedDemoTour />);

    expect(screen.getByRole("heading", { name: "See the system before you run it." })).toBeVisible();
    expect(screen.getAllByText("Recorded synthetic demonstration")).toHaveLength(3);

    const screenshots = [
      ["Completed text analysis with a KYC scam decision and supporting signals", "/showcase/text-analysis.png", "1180", "1282"],
      ["Completed screenshot analysis with extracted OCR text and review evidence", "/showcase/screenshot-analysis.png", "1180", "1421"],
      ["Two synthetic reports linked through one repeated masked URL", "/showcase/relationship-graph.png", "1180", "1163"],
    ] as const;
    for (const [name, src, width, height] of screenshots) {
      const image = screen.getByRole("img", { name });
      expect(decodeURIComponent(image.getAttribute("src") ?? "")).toContain(src);
      expect(image).toHaveAttribute("width", width);
      expect(image).toHaveAttribute("height", height);
    }

    expect(screen.getAllByRole("link", { name: /open/i })).toHaveLength(3);
    expect(screen.getAllByRole("link", { name: /open analysis/i })).toHaveLength(2);
    expect(screen.getByRole("link", { name: /open relationships/i })).toHaveAttribute("href", "/relationships");
  });
});
