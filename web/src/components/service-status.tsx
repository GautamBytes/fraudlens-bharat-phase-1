"use client";

import { useEffect, useState } from "react";

type State = "checking" | "ready" | "waking" | "offline";

async function readServiceState(): Promise<State> {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (response.ok) return "ready";
    if (response.status === 504 || response.status === 503) return "waking";
    return "offline";
  } catch {
    return "offline";
  }
}

export function ServiceStatus() {
  const [state, setState] = useState<State>("checking");
  const [retryCycle, setRetryCycle] = useState(0);

  const retry = () => {
    setState("checking");
    void readServiceState().then(setState);
  };

  useEffect(() => {
    let active = true;
    void readServiceState().then((nextState) => {
      if (active) setState(nextState);
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (state !== "waking") return;
    const timer = window.setTimeout(() => {
      void readServiceState().then((nextState) => {
        setState(nextState);
        if (nextState === "waking") setRetryCycle((cycle) => cycle + 1);
      });
    }, 10_000);
    return () => window.clearTimeout(timer);
  }, [state, retryCycle]);

  const copy = {
    checking: ["Checking engine", "Connecting to the analysis service"],
    ready: ["Engine ready", "Model, storage and OCR boundary available"],
    waking: ["Engine waking", "Free hosting can take about a minute · retrying automatically in 10 seconds"],
    offline: ["Engine unavailable", "Use the retry or Docker fallback in Run guide"],
  }[state];

  return (
    <div className={`serviceStatus status-${state}`} role="status">
      <span className="statusDot" />
      <span><strong>{copy[0]}</strong><small>{copy[1]}</small></span>
      {(state === "waking" || state === "offline") && (
        <button type="button" onClick={retry}>Retry</button>
      )}
    </div>
  );
}
