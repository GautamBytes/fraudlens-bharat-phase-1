import type { EntityGraph } from "@/lib/contracts";

export function RelationshipGraph({ graph, selectedCaseId, onSelectCase }: { graph: EntityGraph; selectedCaseId?: string | null; onSelectCase?: (caseId: string) => void }) {
  const entity = graph.entity_nodes[0];
  const linkedCaseIds = new Set(
    graph.edges
      .filter((edge) => edge.source === entity?.id || edge.target === entity?.id)
      .map((edge) => edge.source === entity?.id ? edge.target : edge.source),
  );
  const cases = graph.case_nodes.filter((item) => linkedCaseIds.has(item.id)).slice(0, 6);
  if (!entity || cases.length === 0) return <div className="emptyGraph">No repeated masked entity is present yet.</div>;

  const centerY = 145;
  const caseY = cases.map((_, index) => 48 + index * (194 / Math.max(1, cases.length - 1)));
  return (
    <div className="relationshipGraphWorkspace">
    <svg className="relationshipGraph" viewBox="0 0 720 290" role="img" aria-label={`${cases.length} cases linked to ${entity.masked_value}`}>
      <defs><linearGradient id="entityGlow" x1="0" x2="1"><stop stopColor="#ff5a4f" /><stop offset="1" stopColor="#ee766e" /></linearGradient></defs>
      {cases.map((item, index) => <line key={`edge-${item.id}`} x1="220" y1={caseY[index]} x2="470" y2={centerY} className="graphEdge" />)}
      {cases.map((item, index) => <g className={selectedCaseId === item.id ? "graphCaseSelected" : undefined} key={item.id}><rect x="28" y={caseY[index] - 27} width="192" height="54" rx="14" className="caseNode" /><text x="46" y={caseY[index] - 3} className="nodeTitle">{item.predicted_label.replaceAll("_", " ")}</text><text x="46" y={caseY[index] + 15} className="nodeMeta">risk {item.risk_score}/100 · {item.case_id.slice(0, 8)}</text></g>)}
      <g><rect x="470" y="102" width="222" height="86" rx="22" fill="url(#entityGlow)" /><text x="492" y="132" className="entityType">REPEATED {entity.entity_type.toUpperCase()}</text><text x="492" y="158" className="entityValue">{entity.masked_value}</text><text x="492" y="177" className="entityMeta">masked before persistence</text></g>
    </svg>
    <div className="graphCaseIndex" aria-label="Graph cases">
      {cases.map((item) => (
        <button className={selectedCaseId === item.id ? "graphCaseButton graphCaseButtonActive" : "graphCaseButton"} type="button" key={item.id} onClick={() => onSelectCase?.(item.id)}>
          <span>Inspect {item.predicted_label.replaceAll("_", " ")} case {item.case_id.slice(0, 8)}</span>
          <small>{item.risk_score}/100 risk</small>
        </button>
      ))}
    </div>
    </div>
  );
}
