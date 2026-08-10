import Link from "next/link";

import { AnalysisTrace } from "@/components/analysis-trace";
import { RecordedDemoTour } from "@/components/recorded-demo-tour";
import { SignalField } from "@/components/signal-field";
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
        <div className="signalHeroCopy">
          <p className="heroKicker">Explainable cyber-fraud triage</p>
          <h1 id="signal-hero-title">Review suspicious messages.<br /><em>Keep the decision human.</em></h1>
          <p>FraudLens Bharat turns synthetic text and screenshots into masked evidence, visible risk signals, relationship context, and a reviewable complaint draft.</p>
          <div className="heroActions">
            <Link className="primaryButton" href="/analyze">Start guided evaluation</Link>
            <Link className="quietLink" href="/guide">Run the complete project <span>↗</span></Link>
          </div>
        </div>
        <AnalysisTrace />
      </section>

      <section className="homeSection capabilitySection">
        <div className="homeSectionHeading">
          <p className="eyebrow">One system, four evidence views</p>
          <h2>Everything a reviewer needs.<br /><span>Nothing hidden behind a score.</span></h2>
        </div>
        <div className="signalMosaic">
          <article className="mosaicCard mosaicWide">
            <div><span className="mosaicLabel">Text + OCR</span><h3>One path for what you read and what you receive.</h3><p>Pasted messages and bounded PNG/JPEG screenshots return the same evidence model.</p></div>
            <div className="ocrSample"><span>eng + hin</span><strong>Screenshot text</strong><small>Processed in memory · source image discarded</small></div>
          </article>
          <article className="mosaicCard decisionCard"><span className="mosaicLabel">Explainability</span><h3>Signals stay with the result.</h3><div className="signalStack"><span>Urgent language</span><span>Suspicious URL</span><span>Account threat</span></div></article>
          <article className="mosaicCard privacyCard"><span className="mosaicLabel">Privacy</span><strong>OFF</strong><h3>Storage begins disabled.</h3><p>Identifiers are masked before relationship storage.</p></article>
          <article className="mosaicCard relationshipCard"><span className="mosaicLabel">Relationship intelligence</span><h3>Separate cases.<br />One repeated signal.</h3><div className="miniGraph" aria-hidden="true"><i /><i /><i /><span /></div><p>Observed links support review. They do not make the fraud decision.</p></article>
        </div>
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
        <div><p className="eyebrow">Professor evaluation</p><h2>See the full path in six to eight minutes.</h2><p>Run one analysis, inspect the explanation, build a masked relationship, and verify every research boundary.</p></div>
        <div><Link className="primaryButton" href="/analyze">Begin evaluation</Link><Link className="secondaryButton" href="/guide">Open run guide</Link></div>
      </section>
    </main>
  );
}
