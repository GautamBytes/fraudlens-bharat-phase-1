import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./app-shell";

const authState = vi.hoisted(() => ({
  session: null as { user: { email: string } } | null,
  signOut: vi.fn(),
  replace: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("@/lib/auth-client", () => ({
  authClient: {
    useSession: () => ({ data: authState.session, isPending: false }),
    signOut: authState.signOut,
  },
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ replace: authState.replace, refresh: authState.refresh }),
}));

describe("AppShell", () => {
  it("renders the Signal Studio header and an accessible mobile menu", async () => {
    authState.session = null;
    const user = userEvent.setup();
    render(<AppShell><p>Professor workspace</p></AppShell>);

    expect(screen.getByRole("banner")).toHaveClass("siteHeader");
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    expect(screen.getByText("Professor workspace")).toBeVisible();
    expect(screen.queryByText(/engine ready|checking engine/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Safety notice" })).not.toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeVisible();
    expect(screen.getByRole("link", { name: "Professor sign in" })).toHaveAttribute(
      "href",
      "/login",
    );

    await user.click(screen.getByRole("button", { name: "Menu" }));

    expect(screen.getByRole("button", { name: "Close menu" })).toHaveAttribute("aria-expanded", "true");

    await user.keyboard("{Escape}");

    expect(screen.getByRole("button", { name: "Menu" })).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("button", { name: "Menu" })).toHaveFocus();
  });

  it("shows the signed-in professor and supports logout", async () => {
    authState.session = { user: { email: "professor@example.edu" } };
    authState.signOut.mockResolvedValue({ data: { success: true }, error: null });
    const user = userEvent.setup();

    render(<AppShell><p>Professor workspace</p></AppShell>);

    expect(screen.getByText("professor@example.edu")).toBeVisible();
    expect(screen.queryByRole("link", { name: "Professor sign in" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Sign out" }));
    expect(authState.signOut).toHaveBeenCalledOnce();
    expect(authState.replace).toHaveBeenCalledWith("/");
    expect(authState.refresh).toHaveBeenCalledOnce();
  });
});
