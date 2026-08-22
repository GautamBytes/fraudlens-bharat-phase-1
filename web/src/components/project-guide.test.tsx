import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ProjectGuide } from "./project-guide";

describe("ProjectGuide", () => {
  it("offers hosted and reproducible local evaluation paths", () => {
    render(<ProjectGuide />);
    expect(screen.getByRole("heading", { name: /fastest: hosted evaluation/i })).toBeVisible();
    expect(screen.getByRole("heading", { name: /complete: docker evaluation/i })).toBeVisible();
    expect(screen.getByText(/docker compose up --build/)).toBeVisible();
    expect(screen.getByText("FRAUDLENS_API_URL")).toBeVisible();
    expect(screen.getByText(/curl --fail http:\/\/127\.0\.0\.1:8000\/ready/i)).toBeVisible();
    expect(screen.getByText(/npm test -- --run/)).toBeVisible();
    expect(screen.getByText(/reset demo data/i)).toBeVisible();
    expect(screen.getByText(/synthetic examples only/i)).toBeVisible();
    expect(screen.getByRole("link", { name: /open hosted website/i })).toHaveAttribute("href", "https://fraudlens-bharat.vercel.app");
    expect(screen.queryByText(/professor/i)).not.toBeInTheDocument();
  });

  it("copies a run command with visible feedback", async () => {
    const user = userEvent.setup();
    const writeText = vi.spyOn(navigator.clipboard, "writeText");
    render(<ProjectGuide />);

    await user.click(screen.getAllByRole("button", { name: /copy command/i })[0]);

    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("docker compose up --build"));
    expect(screen.getByRole("button", { name: /command copied/i })).toBeVisible();
  });
});
