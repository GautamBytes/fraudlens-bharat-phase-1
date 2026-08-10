import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProfessorGuide } from "./professor-guide";

describe("ProfessorGuide", () => {
  it("offers hosted and reproducible local evaluation paths", () => {
    render(<ProfessorGuide />);
    expect(screen.getByRole("heading", { name: /fastest: hosted evaluation/i })).toBeVisible();
    expect(screen.getByRole("heading", { name: /complete: docker evaluation/i })).toBeVisible();
    expect(screen.getByText("docker compose up --build")).toBeVisible();
    expect(screen.getByText(/synthetic examples only/i)).toBeVisible();
  });
});
