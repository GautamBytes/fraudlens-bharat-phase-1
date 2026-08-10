import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ServiceStatus } from "./service-status";

describe("ServiceStatus", () => {
  afterEach(() => vi.useRealTimers());

  it("automatically retries a waking analysis engine", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(null, { status: 504 }))
      .mockResolvedValueOnce(new Response(null, { status: 504 }))
      .mockResolvedValueOnce(new Response(null, { status: 200 })));

    render(<ServiceStatus />);
    await act(async () => { await Promise.resolve(); });
    expect(screen.getByText("Engine waking")).toBeVisible();
    expect(screen.getByText(/retrying automatically in 10 seconds/i)).toBeVisible();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect(screen.getByText("Engine waking")).toBeVisible();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect(screen.getByText("Engine ready")).toBeVisible();
    expect(fetch).toHaveBeenCalledTimes(3);
  });
});
