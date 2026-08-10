import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DocsFrame } from "./docs-frame";
import { PageIntro } from "./page-intro";
import { SignalField } from "./signal-field";

describe("Signal Studio layout primitives", () => {
  it("renders a focused page introduction with optional actions", () => {
    render(
      <PageIntro
        eyebrow="Live workflow"
        title="Analyze fraud evidence"
        description="Review a synthetic message."
        actions={<button type="button">Start review</button>}
      />,
    );

    expect(screen.getByRole("heading", { level: 1, name: "Analyze fraud evidence" })).toBeVisible();
    expect(screen.getByText("Review a synthetic message.")).toBeVisible();
    expect(screen.getByRole("button", { name: "Start review" })).toBeVisible();
  });

  it("connects documentation indexes to real anchored content", () => {
    const links = [{ href: "#models", label: "Models" }];
    render(
      <DocsFrame index={links} outline={links}>
        <h2 id="models">Models</h2>
      </DocsFrame>,
    );

    expect(screen.getByRole("navigation", { name: "Section index" })).toContainElement(
      screen.getAllByRole("link", { name: "Models" })[0],
    );
    expect(screen.getByRole("complementary", { name: "On this page" })).toBeVisible();
  });

  it("keeps the signal field decorative", () => {
    const { container } = render(<SignalField />);
    expect(container.querySelector(".signalField")).toHaveAttribute("aria-hidden", "true");
  });
});
