import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { analysisResultFixture } from "@/test/fixtures";
import { AnalysisResultView } from "./analysis-result";

describe("AnalysisResultView", () => {
  it("presents decision, evidence, uncertainty, and complaint output", () => {
    render(<AnalysisResultView result={analysisResultFixture} />);

    expect(screen.getByText("KYC scam")).toBeVisible();
    expect(screen.getByText("81% confidence")).toBeVisible();
    expect(screen.getByText("86 / 100")).toBeVisible();
    expect(screen.getByText("fraud-demo.example/kyc", { exact: false })).toBeVisible();
    expect(screen.getByText(/human review remains required/i)).toBeVisible();
    expect(screen.getByText(analysisResultFixture.complaint_draft)).toBeVisible();
  });
});
