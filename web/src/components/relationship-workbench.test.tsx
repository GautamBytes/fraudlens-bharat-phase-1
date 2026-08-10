import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { EntityGraph } from "@/lib/contracts";
import { RelationshipWorkbench } from "./relationship-workbench";

const linkedGraph: EntityGraph = {
  case_nodes: [
    { id: "case:a", case_id: "a", created_at: "2026-08-10T10:00:00Z", predicted_label: "kyc_scam", risk_level: "high", risk_score: 82 },
    { id: "case:b", case_id: "b", created_at: "2026-08-10T10:01:00Z", predicted_label: "courier_scam", risk_level: "high", risk_score: 76 },
  ],
  entity_nodes: [
    { id: "entity:url:shared", entity_type: "url", entity_id: "shared", masked_value: "fraud-demo.example/•••" },
  ],
  edges: [
    { source: "case:a", target: "entity:url:shared" },
    { source: "case:b", target: "entity:url:shared" },
  ],
  components: [{ id: "component:1", node_ids: ["case:a", "case:b", "entity:url:shared"], case_count: 2, entity_count: 1, edge_count: 2, max_risk_score: 82 }],
  summary: { case_count: 2, entity_count: 1, edge_count: 2, component_count: 1, truncated: false },
};

describe("RelationshipWorkbench", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => Promise.resolve(Response.json(linkedGraph))));
  });

  it("renders masked relationship evidence as a graph and accessible table", async () => {
    render(<RelationshipWorkbench initialGraph={linkedGraph} />);

    expect(screen.getByText("2 linked cases")).toBeVisible();
    const metrics = screen.getByRole("region", { name: "Bounded cluster metrics" });
    const signalMap = screen.getByRole("region", { name: "Relationship signal map" });
    expect(metrics.compareDocumentPosition(signalMap) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getAllByText("fraud-demo.example/•••")).toHaveLength(3);
    expect(screen.getByRole("table", { name: /relationship evidence/i })).toBeVisible();
    expect(screen.queryByText(/https:\/\//i)).not.toBeInTheDocument();
  });

  it("builds a synthetic two-case link with storage explicitly enabled", async () => {
    const user = userEvent.setup();
    render(<RelationshipWorkbench initialGraph={null} />);

    await user.click(screen.getByRole("button", { name: /build synthetic link/i }));

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(4));
    expect(fetch).toHaveBeenNthCalledWith(1, "/api/cases", expect.objectContaining({ method: "DELETE" }));
    for (const call of vi.mocked(fetch).mock.calls.slice(1, 3)) {
      expect(JSON.parse(String(call[1]?.body))).toMatchObject({ store_case: true });
    }
    expect(fetch).toHaveBeenLastCalledWith("/api/graph?minimum_case_count=2", expect.objectContaining({ cache: "no-store" }));
  });

  it("maps each case to entities through graph edges rather than array position", () => {
    const graph: EntityGraph = {
      ...linkedGraph,
      case_nodes: [...linkedGraph.case_nodes, { id: "case:c", case_id: "c", created_at: "2026-08-10T10:02:00Z", predicted_label: "fake_job", risk_level: "medium", risk_score: 52 }],
      entity_nodes: [...linkedGraph.entity_nodes, { id: "entity:phone:other", entity_type: "phone", entity_id: "other", masked_value: "+91••••2211" }],
      edges: [...linkedGraph.edges, { source: "case:b", target: "entity:phone:other" }, { source: "case:c", target: "entity:phone:other" }],
    };
    render(<RelationshipWorkbench initialGraph={graph} />);

    const rows = within(screen.getByRole("table", { name: /relationship evidence/i })).getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("fraud-demo.example/•••");
    expect(rows[0]).not.toHaveTextContent("+91••••2211");
    expect(rows[1]).toHaveTextContent("fraud-demo.example/•••, +91••••2211");
    expect(rows[2]).toHaveTextContent("+91••••2211");
  });
});
