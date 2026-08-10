import Link from "next/link";

import { DEFAULT_DEMO_MESSAGE } from "@/lib/demo-data";

export function AnalysisTrace() {
  return (
    <section className="analysisTrace" aria-label="Synthetic analysis trace">
      <div className="traceTopline">
        <span>Live product path</span>
        <span className="traceStatus"><i /> Ready for review</span>
      </div>
      <div className="traceFlow">
        <article className="traceInput">
          <span className="traceLabel">Synthetic message</span>
          <p>{DEFAULT_DEMO_MESSAGE}</p>
        </article>
        <div className="traceConnector" aria-hidden="true"><span>01</span><i /></div>
        <article className="traceSignals">
          <span className="traceLabel">Masked signals</span>
          <div><small>URL</small><strong>fraud-demo.example/•••</strong></div>
          <div><small>Language</small><strong>Urgency · account threat</strong></div>
        </article>
        <div className="traceConnector" aria-hidden="true"><span>02</span><i /></div>
        <article className="traceDecision">
          <span className="traceLabel">Human review</span>
          <strong>KYC scam</strong>
          <p>Evidence and uncertainty stay attached to the decision.</p>
          <Link href="/analyze">Open live analyzer</Link>
        </article>
      </div>
    </section>
  );
}
