import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import GuidePage from "@/app/guide/page";
import ResearchPage from "@/app/research/page";

function expectWorkingSectionIndex() {
  const index = screen.getByRole("navigation", { name: "Section index" });
  for (const link of within(index).getAllByRole("link")) {
    const target = link.getAttribute("href");
    expect(target).toMatch(/^#/);
    expect(document.querySelector(target as string)).not.toBeNull();
  }
  expect(screen.getByRole("complementary", { name: "On this page" })).toBeVisible();
}

describe("documentation pages", () => {
  it("gives the research evidence a working section index", () => {
    render(<ResearchPage />);
    expectWorkingSectionIndex();
    expect(screen.getByRole("link", { name: "Model comparison" })).toHaveAttribute("href", "#comparison");
  });

  it("gives the professor guide a working section index", () => {
    render(<GuidePage />);
    expectWorkingSectionIndex();
    expect(screen.getByRole("link", { name: "Complete local run" })).toHaveAttribute("href", "#docker-run");
  });
});
