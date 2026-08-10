import Link from "next/link";

import { EvidenceRail } from "@/components/evidence-rail";
import { ServiceStatus } from "@/components/service-status";

const CAPABILITIES = [
  ["Text + OCR", "Pasted messages and bounded PNG/JPEG screenshots follow one analysis path."],
  ["Explainable decision", "Confidence, abstention, evidence and visible risk reasons remain together."],
  ["Privacy boundary", "Storage begins off; image bytes are discarded and relationship identifiers are masked."],
] as const;

export default function EvaluatePage() {
  return (
    <main className="pageContent evaluatePage">
      <section className="heroSection">
        <div className="heroCopy">
          <p className="eyebrow">Professor evaluation workspace · Final Phase 1 + Phase 2</p>
          <h1>Turn a suspicious message into evidence a human can review.</h1>
          <p className="heroLead">
            FraudLens Bharat classifies common Indian cyber-fraud messages, recovers complaint evidence,
            explains risk, reads screenshots locally and exposes repeated masked identifiers.
          </p>
          <div className="heroActions">
            <Link className="primaryButton" href="/analyze">Start guided evaluation</Link>
            <Link className="textLink" href="/guide">How to run the complete project →</Link>
          </div>
        </div>
        <div className="heroCaseFile" aria-label="Project boundary">
          <div className="caseFileTop"><span>CASE / CAPSTONE-01</span><span>ASSISTIVE</span></div>
          <div className="casePulse"><span>8</span><small>fraud categories</small></div>
          <dl>
            <div><dt>Inputs</dt><dd>Text + screenshot</dd></div>
            <div><dt>Languages</dt><dd>English · Hindi · Hinglish</dd></div>
            <div><dt>Output</dt><dd>Evidence + draft</dd></div>
            <div><dt>Decision</dt><dd>Human controlled</dd></div>
          </dl>
        </div>
      </section>

      <ServiceStatus />

      <section className="evaluationPath">
        <div className="sectionHeading">
          <div><p className="eyebrow">What to evaluate</p><h2>One traceable analysis path</h2></div>
          <span>Recommended review time: 6–8 minutes</span>
        </div>
        <EvidenceRail activeStep={4} />
      </section>

      <section className="capabilityGrid">
        {CAPABILITIES.map(([title, detail], index) => (
          <article key={title}>
            <span className="cardIndex">0{index + 1}</span>
            <h3>{title}</h3>
            <p>{detail}</p>
          </article>
        ))}
      </section>

      <section className="boundaryCallout">
        <div><span>Research candidate</span><strong>75.0% accuracy</strong><small>Character TF-IDF · 8-row frozen test</small></div>
        <div><span>Deployed runtime</span><strong>50.0% accuracy</strong><small>87.5% coverage after abstention</small></div>
        <p>These are different evaluation targets on a 64-row synthetic fraud-only dataset—not a production claim.</p>
      </section>
    </main>
  );
}
