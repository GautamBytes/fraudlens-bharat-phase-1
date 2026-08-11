"use client";

import { FormEvent, useState } from "react";

import { authClient } from "@/lib/auth-client";

export function SignInForm({ returnTo }: { returnTo: string }) {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    const form = new FormData(event.currentTarget);
    try {
      const result = await authClient.signIn.email({
        email: String(form.get("email") ?? "").trim(),
        password: String(form.get("password") ?? ""),
        callbackURL: returnTo,
      });
      if (!result.error) return;
      setError("Invalid email or password");
    } catch {
      setError("Sign-in service is unavailable");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="authForm" onSubmit={submit}>
      <label className="authField">
        <span>Professor email</span>
        <input name="email" type="email" autoComplete="username" required />
      </label>
      <label className="authField">
        <span>Password</span>
        <input name="password" type="password" autoComplete="current-password" required />
      </label>
      {error ? <p className="errorNotice" role="alert">{error}</p> : null}
      <button className="primaryButton authSubmit" type="submit" disabled={pending}>
        {pending ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
