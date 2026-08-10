import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AnalysisTrace } from "./analysis-trace";

describe("AnalysisTrace", () => {
  it("shows a synthetic input, masked evidence, and human-review output", () => {
    render(<AnalysisTrace />);

    expect(screen.getByRole("region", { name: "Synthetic analysis trace" })).toBeVisible();
    expect(screen.getByText("Synthetic message")).toBeVisible();
    expect(screen.getByText("Masked signals")).toBeVisible();
    expect(screen.getByText(/human review/i)).toBeVisible();
    expect(screen.getByText("fraud-demo.example/•••")).toBeVisible();
    expect(screen.getByRole("link", { name: "Open live analyzer" })).toHaveAttribute("href", "/analyze");
  });
});
