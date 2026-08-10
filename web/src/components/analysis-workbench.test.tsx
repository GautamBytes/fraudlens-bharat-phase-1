import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { analysisResultFixture } from "@/test/fixtures";
import { AnalysisWorkbench } from "./analysis-workbench";

describe("AnalysisWorkbench", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json(analysisResultFixture)),
    );
  });

  it("starts with storage off and analyzes a prepared synthetic message", async () => {
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);

    expect(
      screen.getByRole("checkbox", { name: /store this synthetic analysis/i }),
    ).not.toBeChecked();
    expect(screen.getByRole("heading", { name: "What happens next" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /analyze message/i }));

    expect(await screen.findByText("KYC scam")).toBeVisible();
    expect(screen.getByTestId("analysis-workspace")).toHaveAttribute("data-state", "complete");
    expect(screen.getByRole("heading", { name: /review decision/i })).toBeVisible();
    expect(screen.getByRole("heading", { name: /complaint draft/i })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "What happens next" })).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/analyze",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("rejects a screenshot above the web limit without making a request", async () => {
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);
    await user.click(screen.getByRole("tab", { name: /screenshot/i }));
    const file = new File([new Uint8Array(4_000_001)], "large.png", {
      type: "image/png",
    });

    await user.upload(screen.getByLabelText(/upload screenshot/i), file);

    expect(screen.getByRole("alert")).toHaveTextContent(/under 4 MB/i);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("shows a specific recovery message when the analysis engine is waking", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      Response.json(
        { detail: "Analysis service is still starting" },
        { status: 504 },
      ),
    );
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);

    await user.click(screen.getByRole("button", { name: /analyze message/i }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        /waking the analysis engine/i,
      ),
    );
  });

  it("reports a missing hosted backend as a deployment configuration problem", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      Response.json(
        { detail: "Analysis service is not configured" },
        { status: 503 },
      ),
    );
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);

    await user.click(screen.getByRole("button", { name: /analyze message/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The analysis service is not connected to this website.",
    );
    expect(screen.getByRole("alert")).not.toHaveTextContent(/OCR is unavailable/i);
  });

  it("gives an actionable retry message for an unexpected analysis failure", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      Response.json({ detail: "Unexpected failure" }, { status: 500 }),
    );
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);

    await user.click(screen.getByRole("button", { name: /analyze message/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The analysis could not be completed. Try again in a moment.",
    );
    expect(screen.getByRole("alert")).not.toHaveTextContent(/service status/i);
  });
});
