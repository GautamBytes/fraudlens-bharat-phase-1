import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InterfaceIcon, StatusPill } from "./interface-primitives";

describe("interface primitives", () => {
  it("renders status text with a semantic tone", () => {
    render(<StatusPill tone="safe">Storage off</StatusPill>);

    expect(screen.getByText("Storage off")).toHaveClass("statusPill", "statusPillSafe");
  });

  it("keeps decorative interface icons out of the accessibility tree", () => {
    const { container } = render(<InterfaceIcon name="arrow" />);

    expect(container.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelector("svg")).not.toHaveAttribute("role");
  });
});
