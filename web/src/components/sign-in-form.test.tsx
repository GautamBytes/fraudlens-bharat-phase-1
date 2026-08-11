import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

const signInEmail = vi.fn();

vi.mock("@/lib/auth-client", () => ({
  authClient: { signIn: { email: signInEmail } },
}));

describe("SignInForm", () => {
  it("submits professor credentials and keeps authentication errors generic", async () => {
    const implementation = await import("./sign-in-form").catch(() => null);
    expect(implementation).not.toBeNull();
    if (!implementation) return;

    signInEmail.mockResolvedValue({
      data: null,
      error: { message: "User not found", status: 401 },
    });
    const user = userEvent.setup();
    render(<implementation.SignInForm returnTo="/relationships" />);

    await user.type(screen.getByLabelText("Professor email"), "professor@example.edu");
    await user.type(screen.getByLabelText("Password"), "strong-example-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(signInEmail).toHaveBeenCalledWith({
      email: "professor@example.edu",
      password: "strong-example-password",
      callbackURL: "/relationships",
    });
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid email or password");
    expect(screen.queryByText("User not found")).not.toBeInTheDocument();
  });

  it("recovers from an unavailable authentication service without leaking details", async () => {
    const { SignInForm } = await import("./sign-in-form");
    signInEmail.mockRejectedValue(new Error("postgresql://private-host/fraudlens"));
    const user = userEvent.setup();
    render(<SignInForm returnTo="/analyze" />);

    await user.type(screen.getByLabelText("Professor email"), "professor@example.edu");
    await user.type(screen.getByLabelText("Password"), "strong-example-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Sign-in service is unavailable");
    expect(screen.queryByText(/private-host/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
  });
});
