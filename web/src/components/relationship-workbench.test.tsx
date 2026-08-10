import { render, screen, waitFor } from "@testing-library/react";
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
});
