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
  const [minimumCaseCount, setMinimumCaseCount] = useState(2);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  async function refresh() {
    const response = await fetch(`/api/graph?minimum_case_count=${minimumCaseCount}`, { cache: "no-store" });
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
    try { await responseJson(await fetch("/api/cases", { method: "DELETE" })); setGraph(null); setSelectedCaseId(null); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Could not clear the demo cases."); }
    finally { setPending(false); }
  }

  const summary = graph?.summary;
  const selectedCase = graph?.case_nodes.find((item) => item.id === selectedCaseId);
  const selectedEntityValues = selectedCase && graph
    ? graph.edges
      .filter((edge) => edge.source === selectedCase.id || edge.target === selectedCase.id)
      .map((edge) => edge.source === selectedCase.id ? edge.target : edge.source)
      .map((id) => graph.entity_nodes.find((entity) => entity.id === id)?.masked_value)
      .filter((value): value is string => Boolean(value))
    : [];
  return (
    <div className="relationshipStack">
      <section className="relationshipControls">
        <div>
          <p className="eyebrow">Repeat-campaign investigation</p>
          <h2>{summary ? `${summary.case_count} linked cases` : "Build a privacy-safe link"}</h2>
          <p>Only synthetic messages are retained, and detected values are masked before relationship storage.</p>
        </div>
        <div className="relationshipActions">
          <label>
            Repeated-case threshold
            <select value={minimumCaseCount} onChange={(event) => setMinimumCaseCount(Number(event.target.value))}>
              {[2, 3, 4, 5].map((value) => <option key={value} value={value}>{value} cases</option>)}
            </select>
          </label>
          <div className="controlButtons">
            <button className="primaryButton" disabled={pending} onClick={buildDemo}>{pending ? "Building evidence…" : "Build synthetic link"}</button>
            <button className="secondaryButton" disabled={pending} onClick={() => void refresh()}>Refresh</button>
            <button className="textButton" disabled={pending} onClick={clear}>Clear</button>
          </div>
        </div>
      </section>
      <ol className="relationshipCue" aria-label="Relationship walkthrough">
        <li><span>01</span><div><strong>Build</strong><small>Create two controlled synthetic cases that reuse one URL.</small></div></li>
        <li><span>02</span><div><strong>Inspect</strong><small>See the repeated value connect otherwise separate scam reports.</small></div></li>
        <li><span>03</span><div><strong>Verify</strong><small>Confirm the stored entity stays masked and every edge remains auditable.</small></div></li>
      </ol>
      {error && <div role="alert" className="errorNotice">{error}</div>}
      {graph && graph.components.length > 0 && (
        <section className="clusterMetrics" aria-label="Bounded cluster metrics">
          {graph.components.map((component, index) => (
            <article key={component.id}>
              <span>Cluster {index + 1}</span>
              <strong>{component.case_count} cases · {component.entity_count} repeated entities</strong>
              <small>{component.edge_count} observed links · max risk {component.max_risk_score}/100</small>
            </article>
          ))}
        </section>
      )}
      <section className="graphCanvas" aria-label="Relationship signal map">
        <div className="graphCaption"><span>Observed co-occurrence</span><small>Masked before persistence</small></div>
        <RelationshipGraph graph={graph ?? { case_nodes: [], entity_nodes: [], edges: [], components: [], summary: { case_count: 0, entity_count: 0, edge_count: 0, component_count: 0, truncated: false } }} selectedCaseId={selectedCaseId} onSelectCase={setSelectedCaseId} />
        {selectedCase && (
          <aside className="selectedEvidence" aria-live="polite">
            <div><span>Selected evidence</span><strong>{selectedCase.predicted_label.replaceAll("_", " ")}</strong></div>
            <p>Risk score {selectedCase.risk_score}/100 · case {selectedCase.case_id.slice(0, 8)}</p>
            <small>{selectedEntityValues.length ? `Connected through ${selectedEntityValues.join(", ")}` : "No repeated masked entity"}</small>
          </aside>
        )}
      </section>
      {graph && graph.entity_nodes.length > 0 && (
        <section className="relationshipTableSection">
          <div className="sectionIntro"><p className="eyebrow">Auditable evidence</p><h2>Verify every relationship edge</h2><p>Observational co-occurrence only. The graph does not classify fraud.</p></div>
          <div className="modelTableWrap" tabIndex={0} aria-label="Relationship evidence table; scroll horizontally on small screens">
            <table className="modelTable" aria-label="Relationship evidence">
              <caption className="visuallyHidden">Cases and their edge-linked masked entities</caption>
              <thead><tr><th>Case</th><th>Classification</th><th>Risk</th><th>Shared masked entities</th></tr></thead>
              <tbody>
                {graph.case_nodes.map((caseNode) => {
                  const entityIds = graph.edges.filter((edge) => edge.source === caseNode.id || edge.target === caseNode.id).map((edge) => edge.source === caseNode.id ? edge.target : edge.source);
                  const values = graph.entity_nodes.filter((entity) => entityIds.includes(entity.id)).map((entity) => entity.masked_value);
                  return <tr key={caseNode.id}><td><code>{caseNode.case_id.slice(0, 8)}</code></td><td>{caseNode.predicted_label.replaceAll("_", " ")}</td><td>{caseNode.risk_score}/100</td><td>{values.join(", ") || "No repeated entity"}</td></tr>;
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
