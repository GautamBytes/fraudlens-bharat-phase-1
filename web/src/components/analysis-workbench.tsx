"use client";

import { ChangeEvent, FormEvent, useState } from "react";

import type { AnalysisResult } from "@/lib/contracts";
import { DEFAULT_DEMO_MESSAGE, DEMO_MESSAGES } from "@/lib/demo-data";
import { AnalysisResultView } from "./analysis-result";
import { EvidenceRail } from "./evidence-rail";
import { InterfaceIcon, StatusPill } from "./interface-primitives";

const WEB_IMAGE_MAX_BYTES = 4_000_000;
type InputMode = "text" | "screenshot";

function errorMessage(status: number, detail?: string): string {
  if (status === 504 || detail === "Analysis service is still starting") {
    return "We are waking the analysis engine. Wait about a minute, then try again.";
  }
  if (detail === "Analysis service is not configured") {
    return "The analysis service is not connected to this website.";
  }
  if (status === 413) return "The screenshot must stay under 4 MB for the hosted demo.";
  if (status === 415) return "Use a PNG or JPEG screenshot.";
  if (status === 422) return "No usable message text was found. Try a clearer screenshot.";
  if (status === 503) return "OCR is unavailable on the analysis engine right now.";
  return "The analysis could not be completed. Try again in a moment.";
}

async function requestScreenshotAnalysis(file: File, storeCase: boolean): Promise<Response> {
  const request = () => fetch(`/api/analyze-image?store_case=${storeCase}`, {
    method: "POST",
    headers: { "content-type": file.type },
    body: file,
  });
  const response = await request();
  return response.status === 504 ? request() : response;
}

export function AnalysisWorkbench() {
  const [mode, setMode] = useState<InputMode>("text");
  const [message, setMessage] = useState<string>(DEFAULT_DEMO_MESSAGE);
  const [storeCase, setStoreCase] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function consumeResponse(response: Response) {
    const payload = (await response.json()) as AnalysisResult | { detail?: string };
    if (!response.ok) {
      throw new Error(errorMessage(response.status, "detail" in payload ? payload.detail : undefined));
    }
    setResult(payload as AnalysisResult);
  }

  async function analyzeText(event: FormEvent) {
    event.preventDefault();
    if (!message.trim()) {
      setError("Enter a suspicious message before analyzing it.");
      return;
    }
    setPending(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: message, store_case: storeCase }),
      });
      await consumeResponse(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : errorMessage(500));
    } finally {
      setPending(false);
    }
  }

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setResult(null);
    if (selected && selected.size > WEB_IMAGE_MAX_BYTES) {
      setFile(null);
      setError("Keep the hosted-demo screenshot under 4 MB.");
      return;
    }
    if (selected && !new Set(["image/png", "image/jpeg"]).has(selected.type)) {
      setFile(null);
      setError("Use a PNG or JPEG screenshot.");
      return;
    }
    setError(null);
    setFile(selected);
  }

  async function analyzeScreenshot() {
    if (!file) {
      setError("Choose a PNG or JPEG screenshot before analyzing it.");
      return;
    }
    setPending(true);
    setError(null);
    setResult(null);
    try {
      const response = await requestScreenshotAnalysis(file, storeCase);
      await consumeResponse(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : errorMessage(500));
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="analysisFlow">
      <EvidenceRail activeStep={result ? 4 : pending ? 2 : 1} />

      <div
        className={result ? "analysisWorkspace analysisWorkspaceComplete" : "analysisWorkspace analysisWorkspaceReady"}
        data-state={result ? "complete" : pending ? "pending" : "ready"}
        data-testid="analysis-workspace"
      >
        <div className="workspaceStatusBar">
          <div><span className="statusDot" aria-hidden="true" /><strong>Investigation workspace</strong><small>Calibrated runtime · visible evidence</small></div>
          <StatusPill tone={storeCase ? "warning" : "safe"}>{storeCase ? "Storage enabled" : "Storage off"}</StatusPill>
        </div>
        <section className="inputPanel">
        <div className="panelHeading">
          <div>
            <p className="eyebrow">Evidence intake</p>
            <h2>Start with a suspicious message</h2>
          </div>
          <label className="storageToggle">
            <input
              type="checkbox"
              checked={storeCase}
              onChange={(event) => setStoreCase(event.target.checked)}
            />
            <span><strong>Store this synthetic analysis</strong><small>Required only for relationship mapping</small></span>
          </label>
        </div>

        <div className="tabList" role="tablist" aria-label="Evidence input">
          <button
            role="tab"
            aria-selected={mode === "text"}
            className={mode === "text" ? "tabActive" : ""}
            onClick={() => { setMode("text"); setError(null); }}
            type="button"
          >
            Message text
          </button>
          <button
            role="tab"
            aria-selected={mode === "screenshot"}
            className={mode === "screenshot" ? "tabActive" : ""}
            onClick={() => { setMode("screenshot"); setError(null); }}
            type="button"
          >
            Screenshot
          </button>
        </div>

        {mode === "text" ? (
          <form onSubmit={analyzeText} className="inputBody">
            <div className="demoPicker" aria-label="Prepared synthetic examples">
              {DEMO_MESSAGES.map((demo) => (
                <button
                  type="button"
                  key={demo.label}
                  onClick={() => { setMessage(demo.text); setError(null); setResult(null); }}
                >
                  {demo.label}
                </button>
              ))}
            </div>
            <label htmlFor="message">Suspicious message</label>
            <textarea
              id="message"
              value={message}
              maxLength={20_000}
              onChange={(event) => setMessage(event.target.value)}
            />
            <div className="inputFooter">
              <span>{message.length.toLocaleString()} / 20,000 characters</span>
              <button className="primaryButton" disabled={pending} type="submit">
                {pending ? "Analyzing evidence…" : <>Analyze message <InterfaceIcon name="arrow" /></>}
              </button>
            </div>
          </form>
        ) : (
          <div className="inputBody">
            <label className="uploadZone" htmlFor="screenshot">
              <span className="uploadMark">+</span>
              <strong>{file ? file.name : "Upload screenshot"}</strong>
              <small>PNG or JPEG · hosted limit 4 MB · image bytes are discarded</small>
              <input
                id="screenshot"
                type="file"
                accept="image/png,image/jpeg"
                onChange={selectFile}
              />
            </label>
            <div className="inputFooter">
              <span>English and Hindi OCR</span>
              <button
                className="primaryButton"
                disabled={pending}
                type="button"
                onClick={analyzeScreenshot}
              >
                {pending ? "Reading screenshot…" : "Analyze screenshot"}
              </button>
            </div>
          </div>
        )}

        {error && <div className="errorNotice" role="alert">{error}</div>}
        </section>

        {pending && (
          <div className="analysisPending" role="status" aria-live="polite">
            <div className="pendingMark" aria-hidden="true"><InterfaceIcon name="spark" /></div>
            <div><strong>Analyzing evidence</strong><span>Extracting signals, calibrating confidence, and preparing a reviewable result.</span></div>
            <div className="pendingBars" aria-hidden="true"><i /><i /><i /></div>
          </div>
        )}

        {!result && (
          <aside className="analysisGuide" aria-labelledby="analysis-guide-title">
            <p className="eyebrow">Guided review</p>
            <h2 id="analysis-guide-title">What happens next</h2>
            <ol>
              <li><span>01</span><div><strong>Classify the evidence</strong><small>The calibrated runtime predicts a scam category or abstains when confidence is insufficient.</small></div></li>
              <li><span>02</span><div><strong>Inspect the signals</strong><small>Review detected entities, confidence, risk cues, and the reasons behind the decision.</small></div></li>
              <li><span>03</span><div><strong>Keep a human in control</strong><small>Use the generated draft as a starting point for review—not as an automatic complaint.</small></div></li>
            </ol>
            <div className="analysisGuideBoundary">Storage stays off unless you explicitly enable it.</div>
          </aside>
        )}

        {result && <AnalysisResultView result={result} onReset={() => setResult(null)} />}
      </div>
    </div>
  );
}
