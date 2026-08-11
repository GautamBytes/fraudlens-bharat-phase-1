import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./app-shell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

describe("AppShell", () => {
  it("renders the Signal Studio header and an accessible mobile menu", async () => {
    const user = userEvent.setup();
    render(<AppShell><p>Professor workspace</p></AppShell>);

    expect(screen.getByRole("banner")).toHaveClass("siteHeader");
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    expect(screen.getByText("Professor workspace")).toBeVisible();
    expect(screen.queryByText(/engine ready|checking engine/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Safety notice" })).not.toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Menu" }));

    expect(screen.getByRole("button", { name: "Close menu" })).toHaveAttribute("aria-expanded", "true");

    await user.keyboard("{Escape}");

    expect(screen.getByRole("button", { name: "Menu" })).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("button", { name: "Menu" })).toHaveFocus();
  });
});
