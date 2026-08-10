import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

import { chromium } from "@playwright/test";

const baseURL = process.env.SHOWCASE_BASE_URL ?? "http://127.0.0.1:3000";
const outputDirectory = resolve(process.cwd(), "public", "showcase");

const analysisResult = {
  case_id: "case-demo",
  created_at: "2026-08-10T10:00:00Z",
  original_text: "Your KYC expires today. Verify at https://fraud-demo.example/kyc",
  cleaned_text: "your kyc expires today verify at fraud demo example kyc",
  predicted_label: "kyc_scam",
  confidence: 0.81,
  risk_level: "high",
  risk_score: 86,
  entities: [{ type: "url", value: "fraud-demo[.]example/•••", confidence: 1, source: "regex" }],
  risk_signals: [{ name: "urgency", score: 18, reason: "The message creates immediate time pressure.", evidence: "expires today" }],
  explanation: ["KYC language and an external verification link increased risk."],
  complaint_draft: "I received a suspicious KYC message containing an external verification link. I have not shared credentials or approved a payment. Please review the message and secure the affected account if required.",
  metadata: { prediction_model_version: "tfidf-calibrated-v1", prediction_abstained: false, stored: false },
};

const screenshotResult = {
  ...analysisResult,
  case_id: "case-image-demo",
  original_text: "URGENT: Your KYC expires today. Verify your account at fraud-demo.example/kyc",
  metadata: {
    ...analysisResult.metadata,
    input_source: "image",
    ocr_engine: "Tesseract",
    ocr_languages: "eng+hin",
    source_image_retained: false,
  },
};

const graphResult = {
  case_nodes: [
    { id: "case:one", case_id: "case-kyc", created_at: "2026-08-10T10:00:00Z", predicted_label: "kyc_scam", risk_level: "high", risk_score: 86 },
    { id: "case:two", case_id: "case-courier", created_at: "2026-08-10T10:02:00Z", predicted_label: "courier_scam", risk_level: "high", risk_score: 82 },
  ],
  entity_nodes: [{ id: "url:masked", entity_type: "url", entity_id: `url_${"a".repeat(64)}`, masked_value: "fraud-demo[.]example" }],
  edges: [{ source: "case:one", target: "url:masked" }, { source: "case:two", target: "url:masked" }],
  components: [{ id: "component-1", node_ids: ["case:one", "case:two", "url:masked"], case_count: 2, entity_count: 1, edge_count: 2, max_risk_score: 86 }],
  summary: { case_count: 2, entity_count: 1, edge_count: 2, component_count: 1, truncated: false },
};

async function json(route, payload) {
  await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(payload) });
}

async function prepareCapture(page) {
  await page.addStyleTag({ content: ".siteHeader, .siteFooter { display: none !important; } *, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }" });
  await page.evaluate(() => document.fonts.ready);
}

async function renderSyntheticMessage(context) {
  const source = await context.newPage();
  await source.setViewportSize({ width: 760, height: 400 });
  await source.setContent(`
    <!doctype html>
    <html lang="en">
      <body style="margin:0;background:#0e0e0e;color:#f3f3ef;font-family:Arial,sans-serif">
        <main data-synthetic-input style="width:680px;margin:24px;padding:28px;background:#181817;border:1px solid #41413d;border-radius:18px">
          <p style="margin:0 0 18px;color:#55b9b0;font:700 12px monospace;letter-spacing:.12em">SYNTHETIC MESSAGE</p>
          <h1 style="margin:0 0 18px;font-size:30px">Urgent KYC verification</h1>
          <p style="margin:0;font-size:22px;line-height:1.55">URGENT: Your KYC expires today. Verify your account at fraud-demo.example/kyc</p>
        </main>
      </body>
    </html>
  `);
  const buffer = await source.locator("[data-synthetic-input]").screenshot();
  await source.close();
  return buffer;
}

async function captureText(context) {
  const page = await context.newPage();
  await page.route("**/api/analyze", (route) => json(route, analysisResult));
  await page.goto(`${baseURL}/analyze`, { waitUntil: "networkidle" });
  await prepareCapture(page);
  await page.getByRole("button", { name: "Analyze message" }).click();
  await page.getByRole("heading", { name: "KYC scam" }).waitFor();
  await page.getByTestId("analysis-workspace").screenshot({ path: resolve(outputDirectory, "text-analysis.png") });
  await page.close();
}

async function captureScreenshot(context) {
  const syntheticMessage = await renderSyntheticMessage(context);
  const page = await context.newPage();
  await page.route("**/api/analyze-image**", (route) => json(route, screenshotResult));
  await page.goto(`${baseURL}/analyze`, { waitUntil: "networkidle" });
  await prepareCapture(page);
  await page.getByRole("tab", { name: "Screenshot" }).click();
  await page.getByLabel("Upload screenshot").setInputFiles({
    name: "synthetic-kyc-message.png",
    mimeType: "image/png",
    buffer: syntheticMessage,
  });
  await page.getByRole("button", { name: "Analyze screenshot" }).click();
  await page.getByText("Extracted OCR text").waitFor();
  await page.getByTestId("analysis-workspace").screenshot({ path: resolve(outputDirectory, "screenshot-analysis.png") });
  await page.close();
}

async function captureRelationships(context) {
  const page = await context.newPage();
  await page.route("**/api/cases", (route) => json(route, { deleted_count: 2 }));
  await page.route("**/api/analyze", (route) => json(route, analysisResult));
  await page.route("**/api/graph**", (route) => json(route, graphResult));
  await page.goto(`${baseURL}/relationships`, { waitUntil: "networkidle" });
  await prepareCapture(page);
  await page.getByRole("button", { name: "Build synthetic link" }).click();
  await page.getByRole("heading", { name: "2 linked cases" }).waitFor();
  await page.locator(".relationshipStack").screenshot({ path: resolve(outputDirectory, "relationship-graph.png") });
  await page.close();
}

await mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1440, height: 1050 }, colorScheme: "dark", deviceScaleFactor: 1 });

try {
  await captureText(context);
  await captureScreenshot(context);
  await captureRelationships(context);
} finally {
  await context.close();
  await browser.close();
}

console.log(`Captured three synthetic showcase views in ${outputDirectory}`);
