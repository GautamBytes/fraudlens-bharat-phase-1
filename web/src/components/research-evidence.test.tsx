import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResearchEvidence } from "./research-evidence";

describe("ResearchEvidence", () => {
  it("keeps experimental and deployed metrics visibly separate", () => {
    render(<ResearchEvidence />);

    expect(screen.getByRole("heading", { name: /experimental candidate/i })).toBeVisible();
    expect(screen.getByText("75.0%", { selector: "strong" })).toBeVisible();
    expect(screen.getByRole("heading", { name: /deployed calibrated model/i })).toBeVisible();
    expect(screen.getByText("50.0%", { selector: "strong" })).toBeVisible();
    expect(screen.getByText(/64-row synthetic fraud-only bootstrap; 8 test rows/i)).toBeVisible();
    expect(screen.getByText(/committed artifact bundle · 211 KB/i)).toBeVisible();
    expect(screen.getByText(/not a production accuracy claim/i)).toBeVisible();
    expect(screen.getByText(/methodology and validity checks/i)).toBeVisible();
    const signal = screen.getByRole("region", { name: "Research metric signal" });
    expect(signal).toHaveTextContent("Accuracy");
    expect(signal).toHaveTextContent("Macro-F1");
    expect(signal).toHaveTextContent("Coverage");
  });

  it("explains why accuracy alone is insufficient", () => {
    render(<ResearchEvidence />);
    expect(screen.getByText(/macro-f1 weights every scam class equally/i)).toBeVisible();
    expect(screen.getByText(/coverage shows how often the model is willing to decide/i)).toBeVisible();
  });
});
