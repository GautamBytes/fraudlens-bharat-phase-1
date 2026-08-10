import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteFooter } from "./site-footer";

describe("SiteFooter", () => {
  it("closes every page with safety guidance and the exact author contacts", () => {
    render(<SiteFooter />);

    expect(screen.getByRole("contentinfo")).toHaveTextContent("Educational prototype · Synthetic evidence only");
    expect(screen.getByRole("contentinfo")).toHaveTextContent("Do not enter real personal, banking or victim information.");

    const contacts = [
      ["LinkedIn", "https://www.linkedin.com/in/gautam-manchandani/"],
      ["GitHub", "https://github.com/GautamBytes"],
      ["X", "https://x.com/GautamM96"],
    ] as const;

    for (const [name, href] of contacts) {
      expect(screen.getByRole("link", { name })).toHaveAttribute("href", href);
      expect(screen.getByRole("link", { name })).toHaveAttribute("target", "_blank");
      expect(screen.getByRole("link", { name })).toHaveAttribute("rel", "noreferrer");
    }
  });
});
