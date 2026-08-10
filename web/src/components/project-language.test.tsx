import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import EvaluatePage from "@/app/page";
import RelationshipsPage from "@/app/relationships/page";

describe("single-project language", () => {
  it("presents the landing page without phase numbering", () => {
    render(<EvaluatePage />);

    expect(screen.getByText("Explainable cyber-fraud triage")).toBeVisible();
    expect(screen.queryByText(/phase 1|phase 2/i)).not.toBeInTheDocument();
  });

  it("presents relationship intelligence without a phase label", () => {
    render(<RelationshipsPage />);

    expect(screen.getByText("Relationship intelligence")).toBeVisible();
    expect(screen.queryByText(/phase 1|phase 2/i)).not.toBeInTheDocument();
  });
});
