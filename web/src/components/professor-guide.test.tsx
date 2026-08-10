import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProfessorGuide } from "./professor-guide";

describe("ProfessorGuide", () => {
  it("offers hosted and reproducible local evaluation paths", () => {
    render(<ProfessorGuide />);
    expect(screen.getByRole("heading", { name: /fastest: hosted evaluation/i })).toBeVisible();
    expect(screen.getByRole("heading", { name: /complete: docker evaluation/i })).toBeVisible();
    expect(screen.getByText(/docker compose up --build/)).toBeVisible();
    expect(screen.getByText("FRAUDLENS_API_URL")).toBeVisible();
    expect(screen.getByText(/curl --fail http:\/\/127\.0\.0\.1:8000\/ready/i)).toBeVisible();
    expect(screen.getByText(/npm test -- --run/)).toBeVisible();
    expect(screen.getByText(/reset demo data/i)).toBeVisible();
    expect(screen.getByText(/synthetic examples only/i)).toBeVisible();
    expect(screen.getByRole("heading", { name: "Open the project" })).toBeVisible();
    expect(screen.queryByText(/engine ready|check engine status/i)).not.toBeInTheDocument();
    const paths = screen.getByRole("navigation", { name: "Evaluation paths" });
    expect(paths).toHaveTextContent("Hosted");
    expect(paths).toHaveTextContent("Docker");
    expect(paths).toHaveTextContent("Development");
  });
});
