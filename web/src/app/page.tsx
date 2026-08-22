import Link from "next/link";

import { AnalysisTrace } from "@/components/analysis-trace";
import { RecordedDemoTour } from "@/components/recorded-demo-tour";
import { SignalField } from "@/components/signal-field";
import { InterfaceIcon, StatusPill } from "@/components/interface-primitives";
import { RESEARCH_MODELS, RESEARCH_SNAPSHOT } from "@/lib/research-data";

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function EvaluatePage() {
  const candidate = RESEARCH_MODELS[2];
  const deployed = RESEARCH_MODELS[4];

  return (
    <main className="homePage">
      <section className="signalHero" aria-labelledby="signal-hero-title">
        <SignalField />
        <div className="heroLayout">
          <div className="signalHeroCopy">
            <div className="heroKicker"><StatusPill tone="safe">Human-controlled</StatusPill><span>Explainable cyber-fraud triage</span></div>
            <h1 id="signal-hero-title">Turn suspicious messages into <em>reviewable evidence.</em></h1>
            <p>Analyze synthetic text or screenshots, expose the signals behind each result, mask sensitive identifiers, and connect repeated campaign evidence without automating the final decision.</p>
            <div className="heroActions">
              <Link className="primaryButton" href="/analyze">Analyze synthetic evidence <InterfaceIcon name="arrow" /></Link>
              <Link className="secondaryButton" href="/guide">View run guide</Link>
            </div>
            <div className="heroBoundary">
              <span><InterfaceIcon name="shield" /> Storage off by default</span>
              <span>Text + screenshot OCR</span>
              <span>Human review required</span>
            </div>
          </div>
          <AnalysisTrace />
        </div>
      </section>

      <section className="credibilityStrip" aria-label="Project capabilities">
        <span>8 scam categories</span><span>English + Hindi OCR</span><span>Calibrated abstention</span><span>Masked relationship graph</span><span>Reproducible evaluation</span>
      </section>

      <section className="homeSection workflowSection">
        <div className="homeSectionHeading">
          <p className="eyebrow">Evidence pipeline</p>
          <h2>From raw message to accountable review.</h2>
          <p>Each stage preserves context so a reviewer can inspect what the system saw, why it reacted, and what still requires judgment.</p>
        </div>
        <ol className="workflowGrid">
          <li><span>01</span><div className="workflowIcon"><InterfaceIcon name="spark" /></div><h3>Ingest</h3><p>Paste a synthetic message or upload a bounded PNG/JPEG screenshot.</p></li>
          <li><span>02</span><div className="workflowIcon"><InterfaceIcon name="shield" /></div><h3>Extract</h3><p>Recover text, entities, URLs, urgency cues, and evidence metadata.</p></li>
          <li><span>03</span><div className="workflowIcon"><InterfaceIcon name="spark" /></div><h3>Explain</h3><p>Return a calibrated category, confidence, risk score, and visible reasons.</p></li>
          <li><span>04</span><div className="workflowIcon"><InterfaceIcon name="check" /></div><h3>Review</h3><p>Inspect the complaint draft and relationship context before acting.</p></li>
        </ol>
      </section>

      <RecordedDemoTour />

      <section className="homeSection researchBoundary">
        <div className="boundaryHeading"><p className="eyebrow">Honest by design</p><h2>The research result and the deployed result are different claims.</h2></div>
        <div className="boundaryModels">
          <article><span>Experimental candidate</span><strong>{percent(candidate.accuracy)}</strong><small>accuracy · character TF-IDF</small></article>
          <div className="boundaryDivider"><span>compared on</span><strong>{RESEARCH_SNAPSHOT.dataset.test_rows}</strong><small>frozen test rows</small></div>
          <article><span>Deployed calibrated runtime</span><strong>{percent(deployed.accuracy)}</strong><small>accuracy · {percent(deployed.coverage)} coverage</small></article>
        </div>
        <p className="boundaryNote">{RESEARCH_SNAPSHOT.dataset.rows}-row synthetic fraud-only bootstrap, one test row per class, and no legitimate label. These figures support internal comparison, not a production accuracy claim.</p>
        <Link className="quietLink" href="/research">Read the complete research evidence <span>→</span></Link>
      </section>

      <section className="homeCta">
        <div><p className="eyebrow">Start an investigation</p><h2>Follow the evidence. Keep the judgment yours.</h2><p>Run one analysis, inspect the explanation, build a masked relationship, and verify every research boundary.</p></div>
        <div><Link className="primaryButton" href="/analyze">Analyze evidence <InterfaceIcon name="arrow" /></Link><Link className="secondaryButton" href="/guide">Open run guide</Link></div>
      </section>
    </main>
  );
}
