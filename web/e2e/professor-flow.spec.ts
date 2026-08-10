import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const result = {
  case_id: "demo-e2e",
  created_at: "2026-08-10T10:00:00Z",
  original_text: "Synthetic KYC warning",
  cleaned_text: "synthetic kyc warning",
  predicted_label: "kyc_scam",
  confidence: 0.81,
  risk_level: "high",
  risk_score: 86,
  entities: [{ type: "url", value: "fraud-demo.example/•••", confidence: 1, source: "pattern" }],
  risk_signals: [{ name: "urgent_language", score: 20, reason: "Urgent language", evidence: "today" }],
  explanation: ["KYC and account-blocking language influenced the decision."],
  complaint_draft: "I received a synthetic suspicious KYC message for evaluation.",
  metadata: { stored: false, decision_source: "calibrated_model" },
};

const linkedGraph = {
  case_nodes: [
    { id: "case:a", case_id: "case-a", created_at: "2026-08-10T10:00:00Z", predicted_label: "kyc_scam", risk_level: "high", risk_score: 82 },
    { id: "case:b", case_id: "case-b", created_at: "2026-08-10T10:01:00Z", predicted_label: "courier_scam", risk_level: "high", risk_score: 76 },
  ],
  entity_nodes: [{ id: "entity:url:shared", entity_type: "url", entity_id: "shared", masked_value: "fraud-demo.example/•••" }],
  edges: [{ source: "case:a", target: "entity:url:shared" }, { source: "case:b", target: "entity:url:shared" }],
  components: [{ id: "component:1", node_ids: ["case:a", "case:b", "entity:url:shared"], case_count: 2, entity_count: 1, edge_count: 2, max_risk_score: 82 }],
  summary: { case_count: 2, entity_count: 1, edge_count: 2, component_count: 1, truncated: false },
};

test("professor can move from overview to an explainable analysis", async ({ page }) => {
  await page.route("**/api/health", (route) => route.fulfill({ json: { status: "ok", service: "fraudlens-bharat", version: "1.0.0" } }));
  await page.route("**/api/analyze", (route) => route.fulfill({ json: result }));

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /turn a suspicious message into evidence/i })).toBeVisible();
  await expect(page.getByText("Engine ready")).toBeVisible();

  await page.getByRole("link", { name: /start guided evaluation/i }).click();
  await page.getByRole("button", { name: /analyze message/i }).click();
  await expect(page.getByRole("heading", { name: "KYC scam" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /complaint draft/i })).toBeVisible();
  await expect(page.getByText("Not stored")).toBeVisible();
});

test("research and run guidance expose the evidence boundary", async ({ page }) => {
  await page.route("**/api/health", (route) => route.fulfill({ json: { status: "ok", service: "fraudlens-bharat", version: "1.0.0" } }));
  await page.goto("/research");
  await expect(page.getByText(/64-row synthetic fraud-only bootstrap; 8 test rows/i)).toBeVisible();
  await expect(page.getByText(/not a production accuracy claim/i)).toBeVisible();
  await page.goto("/guide");
  await expect(page.getByRole("heading", { name: /hosted evaluation/i })).toBeVisible();
  await expect(page.getByText(/docker compose up --build/)).toBeVisible();
});

test("screenshot intake rejects a payload above the hosted boundary", async ({ page }) => {
  await page.goto("/analyze");
  await page.getByRole("tab", { name: "Screenshot" }).click();
  await page.getByLabel(/upload screenshot/i).setInputFiles({
    name: "too-large.png",
    mimeType: "image/png",
    buffer: Buffer.alloc(4_000_001),
  });
  await expect(page.locator(".errorNotice[role=alert]")).toContainText("under 4 MB");
});

test("professor can seed and reset the masked relationship demo", async ({ page }) => {
  await page.route("**/api/cases", (route) => route.fulfill({ json: { deleted_count: 2 } }));
  await page.route("**/api/analyze", (route) => route.fulfill({ json: result }));
  await page.route("**/api/graph**", (route) => route.fulfill({ json: linkedGraph }));
  await page.goto("/relationships");
  await page.getByRole("button", { name: /build synthetic link/i }).click();
  await expect(page.getByRole("heading", { name: "2 linked cases" })).toBeVisible();
  await expect(page.getByRole("table", { name: /relationship evidence/i })).toContainText("fraud-demo.example/•••");
  await page.getByRole("button", { name: "Clear" }).click();
  await expect(page.getByText(/no repeated masked entity/i)).toBeVisible();
});

test("mobile navigation and keyboard focus remain usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Menu" }).click();
  await expect(page.getByRole("link", { name: /research/i })).toBeVisible();
  await page.getByRole("link", { name: /analyze/i }).click();
  await expect(page.getByRole("heading", { name: /analyze fraud evidence/i })).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
});

test("major professor routes have no automatically detectable accessibility violations", async ({ page }) => {
  await page.route("**/api/health", (route) => route.fulfill({ json: { status: "ok", service: "fraudlens-bharat", version: "1.0.0" } }));
  for (const path of ["/", "/analyze", "/relationships", "/research", "/guide"]) {
    await page.goto(path);
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations, `${path}: ${results.violations.map((item) => item.id).join(", ")}`).toEqual([]);
  }
});
