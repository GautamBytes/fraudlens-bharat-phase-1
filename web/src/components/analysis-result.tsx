"use client";

import { useState } from "react";

import type { AnalysisResult } from "@/lib/contracts";

function titleCaseLabel(label: string): string {
  if (label === "kyc_scam") return "KYC scam";
  return label
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function AnalysisResultView({ result }: { result: AnalysisResult }) {
  const [copied, setCopied] = useState(false);
  const abstained = result.metadata.prediction_abstained === true;

  async function copyDraft() {
    await navigator.clipboard.writeText(result.complaint_draft);
    setCopied(true);
  }

  return (
    <section className="resultPanel resultReveal" aria-live="polite">
      <div className="resultHeading">
        <div>
          <p className="eyebrow">Analysis complete</p>
          <h2>{abstained ? "Needs manual classification" : titleCaseLabel(result.predicted_label)}</h2>
        </div>
        <span className={`riskBadge risk-${result.risk_level}`}>
          {result.risk_level} risk
        </span>
      </div>

      <div className="metricStrip">
        <div>
          <span>Model confidence</span>
          <strong>{percent(result.confidence)} confidence</strong>
        </div>
        <div>
          <span>Risk score</span>
          <strong>{Math.round(result.risk_score)} / 100</strong>
        </div>
        <div>
          <span>Decision mode</span>
          <strong>{abstained ? "Abstained" : "Model accepted"}</strong>
        </div>
        <div>
          <span>Retention</span>
          <strong>{result.metadata.stored === true ? "Stored with consent" : "Not stored"}</strong>
        </div>
      </div>

      {result.metadata.input_source === "image" && (
        <div className="ocrExtract">
          <div className="sectionLabel">Extracted OCR text</div>
          <p>{result.original_text}</p>
          <small>
            {String(result.metadata.ocr_engine ?? "Tesseract")} · {String(result.metadata.ocr_languages ?? "eng+hin")}
          </small>
        </div>
      )}

      <div className="resultGrid">
        <div className="resultColumn">
          <section>
            <div className="sectionLabel">Evidence recovered</div>
            {result.entities.length ? (
              <div className="entityList">
                {result.entities.map((entity, index) => (
                  <div className="entityRow" key={`${entity.type}-${entity.value}-${index}`}>
                    <span>{entity.type.replace("_", " ")}</span>
                    <strong>{entity.value}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <p className="emptyCopy">No structured entities were detected.</p>
            )}
          </section>

          <section>
            <div className="sectionLabel">Why it was flagged</div>
            <ul className="reasonList">
              {result.explanation.map((reason) => <li key={reason}>{reason}</li>)}
            </ul>
          </section>

          {result.risk_signals.length > 0 && (
            <section>
              <div className="sectionLabel">Risk signals</div>
              <div className="signalList">
                {result.risk_signals.map((signal) => (
                  <article key={`${signal.name}-${signal.reason}`}>
                    <div>
                      <strong>{signal.name.replaceAll("_", " ")}</strong>
                      <span>+{signal.score}</span>
                    </div>
                    <p>{signal.reason}</p>
                  </article>
                ))}
              </div>
            </section>
          )}
        </div>

        <aside className="draftCard">
          <div className="sectionLabel">Human-ready output</div>
          <h3>Complaint draft</h3>
          <p>{result.complaint_draft}</p>
          <button className="secondaryButton" type="button" onClick={copyDraft}>
            {copied ? "Copied" : "Copy complaint draft"}
          </button>
          <div className="humanBoundary">
            <strong>Human review remains required.</strong>
            <span>FraudLens does not file a complaint or make a legal decision.</span>
          </div>
        </aside>
      </div>
    </section>
  );
}
