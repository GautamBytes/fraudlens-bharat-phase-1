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
    expect(screen.getByText("Storage off")).toBeVisible();
    expect(screen.getByRole("heading", { name: "What happens next" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /analyze message/i }));

    expect(await screen.findByText("KYC scam")).toBeVisible();
    expect(screen.getByTestId("analysis-workspace")).toHaveAttribute("data-state", "complete");
    expect(screen.getByRole("heading", { name: /review decision/i })).toBeVisible();
    expect(screen.getByRole("heading", { name: /complaint draft/i })).toBeVisible();
    expect(screen.getByRole("button", { name: /analyze another message/i })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "What happens next" })).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/analyze",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("announces progress while evidence is being analyzed", async () => {
    vi.mocked(fetch).mockReturnValueOnce(new Promise(() => undefined));
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);

    await user.click(screen.getByRole("button", { name: /analyze message/i }));

    expect(screen.getByRole("status")).toHaveTextContent(/analyzing evidence/i);
    expect(screen.getByTestId("analysis-workspace")).toHaveAttribute("data-state", "pending");
  });

  it("returns to evidence intake from a completed result", async () => {
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);

    await user.click(screen.getByRole("button", { name: /analyze message/i }));
    await user.click(await screen.findByRole("button", { name: /analyze another message/i }));

    expect(screen.getByRole("heading", { name: "What happens next" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: /review decision/i })).not.toBeInTheDocument();
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

  it("retries screenshot analysis once when the analysis engine is waking", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        Response.json(
          { detail: "Analysis service is still starting" },
          { status: 504 },
        ),
      )
      .mockResolvedValueOnce(Response.json(analysisResultFixture));
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);
    await user.click(screen.getByRole("tab", { name: /screenshot/i }));
    const file = new File([new Uint8Array([137, 80, 78, 71])], "message.png", {
      type: "image/png",
    });

    await user.upload(screen.getByLabelText(/upload screenshot/i), file);
    await user.click(screen.getByRole("button", { name: /analyze screenshot/i }));

    expect(await screen.findByText("KYC scam")).toBeVisible();
    expect(fetch).toHaveBeenCalledTimes(2);
    const [firstUrl, firstOptions] = vi.mocked(fetch).mock.calls[0];
    const [secondUrl, secondOptions] = vi.mocked(fetch).mock.calls[1];
    expect(secondUrl).toBe(firstUrl);
    expect(secondOptions).toEqual(firstOptions);
    expect(firstOptions).toEqual(
      expect.objectContaining({
        method: "POST",
        headers: { "content-type": "image/png" },
        body: file,
      }),
    );
  });

  it("stops screenshot retries after a second waking response", async () => {
    vi.mocked(fetch).mockResolvedValue(
      Response.json(
        { detail: "Analysis service is still starting" },
        { status: 504 },
      ),
    );
    const user = userEvent.setup();
    render(<AnalysisWorkbench />);
    await user.click(screen.getByRole("tab", { name: /screenshot/i }));
    const file = new File([new Uint8Array([137, 80, 78, 71])], "message.png", {
      type: "image/png",
    });

    await user.upload(screen.getByLabelText(/upload screenshot/i), file);
    await user.click(screen.getByRole("button", { name: /analyze screenshot/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /waking the analysis engine/i,
    );
    expect(fetch).toHaveBeenCalledTimes(2);
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
    expect(fetch).toHaveBeenCalledTimes(1);
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
