"use client";

import { useState } from "react";
import type { EntityGraph } from "@/lib/contracts";
import { RelationshipGraph } from "./relationship-graph";

const SHARED_URL = "https://fraud-demo.example/repeated-campaign";
const LINKED_DEMOS = [
  `Your KYC expires today. Verify now at ${SHARED_URL} or your account will be blocked.`,
  `Courier parcel held. Pay the release fee immediately at ${SHARED_URL}.`,
];

async function responseJson<T>(response: Response): Promise<T> {
  const payload = await response.json();
  if (!response.ok) throw new Error("The relationship service could not complete this request.");
  return payload as T;
}

export function RelationshipWorkbench({ initialGraph }: { initialGraph: EntityGraph | null }) {
  const [graph, setGraph] = useState(initialGraph);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const response = await fetch("/api/graph?minimum_case_count=2", { cache: "no-store" });
    setGraph(await responseJson<EntityGraph>(response));
  }

  async function buildDemo() {
    setPending(true); setError(null);
    try {
      await responseJson(await fetch("/api/cases", { method: "DELETE" }));
      for (const text of LINKED_DEMOS) {
        await responseJson(await fetch("/api/analyze", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text, store_case: true }) }));
      }
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Relationship demo failed.");
    } finally { setPending(false); }
  }

  async function clear() {
    setPending(true); setError(null);
    try { await responseJson(await fetch("/api/cases", { method: "DELETE" })); setGraph(null); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Could not clear the demo cases."); }
    finally { setPending(false); }
  }

  const summary = graph?.summary;
  return (
    <div className="relationshipStack">
      <section className="relationshipControls">
        <div><p className="eyebrow">Repeat-campaign investigation</p><h2>{summary ? `${summary.case_count} linked cases` : "Build a privacy-safe link"}</h2><p>Only synthetic messages are retained, and detected values are masked before relationship storage.</p></div>
        <div className="controlButtons"><button className="primaryButton" disabled={pending} onClick={buildDemo}>{pending ? "Building evidence…" : "Build synthetic link"}</button><button className="secondaryButton" disabled={pending} onClick={() => void refresh()}>Refresh</button><button className="textButton" disabled={pending} onClick={clear}>Clear</button></div>
      </section>
      {error && <div role="alert" className="errorNotice">{error}</div>}
      <section className="graphCanvas"><RelationshipGraph graph={graph ?? { case_nodes: [], entity_nodes: [], edges: [], components: [], summary: { case_count: 0, entity_count: 0, edge_count: 0, component_count: 0, truncated: false } }} /></section>
      {graph && graph.entity_nodes.length > 0 && <section className="relationshipTableSection"><div className="sectionIntro"><p className="eyebrow">Auditable fallback</p><h2>Relationship evidence table</h2></div><div className="modelTableWrap"><table className="modelTable" aria-label="Relationship evidence"><thead><tr><th>Case</th><th>Classification</th><th>Risk</th><th>Shared masked entity</th></tr></thead><tbody>{graph.case_nodes.map((caseNode) => <tr key={caseNode.id}><td><code>{caseNode.case_id.slice(0, 8)}</code></td><td>{caseNode.predicted_label.replaceAll("_", " ")}</td><td>{caseNode.risk_score}/100</td><td>{graph.entity_nodes[0].masked_value}</td></tr>)}</tbody></table></div></section>}
    </div>
  );
}
