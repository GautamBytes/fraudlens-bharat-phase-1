import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import EvaluatePage from "@/app/page";

describe("landing page", () => {
  it("presents the complete evidence workflow before asking for analysis", () => {
    render(<EvaluatePage />);

    expect(screen.getByRole("heading", { level: 1, name: /turn suspicious messages into reviewable evidence/i })).toBeVisible();
    expect(screen.getByRole("link", { name: /analyze synthetic evidence/i })).toHaveAttribute("href", "/analyze");
    expect(screen.getByText(/storage off by default/i)).toBeVisible();
    expect(screen.getByRole("heading", { name: /from raw message to accountable review/i })).toBeVisible();
    expect(screen.getByRole("heading", { name: /see the evidence before you run it/i })).toBeVisible();
    expect(screen.queryByText(/professor/i)).not.toBeInTheDocument();
  });
});
