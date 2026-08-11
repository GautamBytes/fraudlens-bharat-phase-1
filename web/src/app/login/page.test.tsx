import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/components/sign-in-form", () => ({
  SignInForm: ({ returnTo }: { returnTo: string }) => <p>Return to {returnTo}</p>,
}));

describe("professor login page", () => {
  it("presents the controlled-demo boundary and sanitizes the return destination", async () => {
    const implementation = await import("./page").catch(() => null);
    expect(implementation).not.toBeNull();
    if (!implementation) return;

    const view = await implementation.default({
      searchParams: Promise.resolve({ returnTo: "//attacker.example" }),
    });
    render(view);

    expect(screen.getByRole("heading", { name: "Professor access" })).toBeVisible();
    expect(screen.getByText("Return to /analyze")).toBeVisible();
    expect(screen.getByText(/synthetic evidence only/i)).toBeVisible();
    expect(screen.queryByRole("link", { name: /sign up/i })).not.toBeInTheDocument();
  });
});
