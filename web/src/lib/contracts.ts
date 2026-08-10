export type Entity = {
  type: string;
  value: string;
  confidence: number;
  source: string;
};

export type RiskSignal = {
  name: string;
  score: number;
  reason: string;
  evidence: string | null;
};

export type AnalysisResult = {
  case_id: string;
  created_at: string;
  original_text: string;
  cleaned_text: string;
  predicted_label: string;
  confidence: number;
  risk_level: "low" | "medium" | "high";
  risk_score: number;
  entities: Entity[];
  risk_signals: RiskSignal[];
  explanation: string[];
  complaint_draft: string;
  metadata: Record<string, unknown>;
};

export type CaseNode = {
  id: string;
  case_id: string;
  created_at: string;
  predicted_label: string;
  risk_level: string;
  risk_score: number;
};

export type EntityNode = {
  id: string;
  entity_type: string;
  entity_id: string;
  masked_value: string;
};

export type GraphEdge = { source: string; target: string };

export type GraphSummary = {
  case_count: number;
  entity_count: number;
  edge_count: number;
  component_count: number;
  truncated: boolean;
};

export type EntityGraph = {
  case_nodes: CaseNode[];
  entity_nodes: EntityNode[];
  edges: GraphEdge[];
  components: Array<{
    id: string;
    node_ids: string[];
    case_count: number;
    entity_count: number;
    edge_count: number;
    max_risk_score: number;
  }>;
  summary: GraphSummary;
};

export type ServiceStatus = {
  status: "ok" | "ready";
  service: string;
  version: string;
};
