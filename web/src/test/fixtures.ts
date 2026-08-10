import type { AnalysisResult, EntityGraph } from "@/lib/contracts";

export const analysisResultFixture: AnalysisResult = {
  case_id: "case-demo",
  created_at: "2026-08-10T10:00:00Z",
  original_text: "Your KYC expires today. Verify at https://fraud-demo.example/kyc",
  cleaned_text: "your kyc expires today verify at fraud demo example kyc",
  predicted_label: "kyc_scam",
  confidence: 0.81,
  risk_level: "high",
  risk_score: 86,
  entities: [
    {
      type: "url",
      value: "https://fraud-demo.example/kyc",
      confidence: 1,
      source: "regex",
    },
  ],
  risk_signals: [
    {
      name: "urgency",
      score: 18,
      reason: "The message creates immediate time pressure.",
      evidence: "expires today",
    },
  ],
  explanation: ["KYC language and an external verification link increased risk."],
  complaint_draft: "I received a suspicious KYC message containing a verification link.",
  metadata: {
    prediction_model_version: "tfidf-calibrated-v1",
    prediction_abstained: false,
    stored: false,
  },
};

export const graphFixture: EntityGraph = {
  case_nodes: [
    {
      id: "case:one",
      case_id: "one",
      created_at: "2026-08-10T10:00:00Z",
      predicted_label: "kyc_scam",
      risk_level: "high",
      risk_score: 86,
    },
    {
      id: "case:two",
      case_id: "two",
      created_at: "2026-08-10T10:02:00Z",
      predicted_label: "courier_scam",
      risk_level: "high",
      risk_score: 82,
    },
  ],
  entity_nodes: [
    {
      id: "url:masked",
      entity_type: "url",
      entity_id: `url_${"a".repeat(64)}`,
      masked_value: "fraud-demo.example",
    },
  ],
  edges: [
    { source: "case:one", target: "url:masked" },
    { source: "case:two", target: "url:masked" },
  ],
  components: [
    {
      id: "component-1",
      node_ids: ["case:one", "case:two", "url:masked"],
      case_count: 2,
      entity_count: 1,
      edge_count: 2,
      max_risk_score: 86,
    },
  ],
  summary: {
    case_count: 2,
    entity_count: 1,
    edge_count: 2,
    component_count: 1,
    truncated: false,
  },
};
