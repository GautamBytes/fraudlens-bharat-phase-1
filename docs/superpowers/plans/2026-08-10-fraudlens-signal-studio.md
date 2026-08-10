# FraudLens Signal Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dashboard-like FraudLens web UI with the approved Signal Studio experience while preserving every professor workflow and backend contract.

**Architecture:** Keep the existing Next.js route handlers and stateful workbench components. Introduce small presentational components for the global shell, landing-page signal trace, page introductions, and documentation frames; compose existing data views inside the new layouts. Use semantic component tests for structure and Playwright for responsive, keyboard, accessibility, and complete-flow verification.

**Tech Stack:** Next.js 16.3, React 19.2, TypeScript 5.9, CSS, Vitest, Testing Library, Playwright, axe-core.

## Global Constraints

- Preserve every FastAPI route, request limit, demo-key boundary, and Python behavior.
- Use Canvas black `#0E0E0E`, Raised surface `#181817`, Primary text `#F3F3EF`, Muted text `#9A9A94`, Signal coral `#FF604F`, Review amber `#F3A712`, Evidence teal `#55B9B0`, and Hairline `#2B2B29`.
- Ship dark mode only; use small surface-luminance changes instead of white cards.
- Use Instrument Sans for display/body and IBM Plex Mono for evidence metadata.
- Preserve the synthetic-data, small-dataset, abstention, privacy, and human-review boundaries.
- Support 1440, 1024, 768, and 390 pixel widths, 200% zoom, visible focus, and reduced motion.
- Do not copy source code, assets, logos, or illustrations from `swift-ai-sdk.dev`.

---

### Task 1: Signal Studio shell and shared layout primitives

**Files:**
- Create: `web/src/components/app-shell.test.tsx`
- Create: `web/src/components/page-intro.tsx`
- Create: `web/src/components/docs-frame.tsx`
- Create: `web/src/components/signal-field.tsx`
- Modify: `web/src/components/app-shell.tsx`
- Modify: `web/src/app/layout.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: `usePathname()` and existing five route definitions.
- Produces: `PageIntro`, `DocsFrame`, and `SignalField` presentational components plus a horizontal `AppShell` with an accessible mobile menu.

- [ ] **Step 1: Write the failing shell test**

```tsx
it("renders horizontal navigation and an accessible mobile menu", async () => {
  render(<AppShell><p>content</p></AppShell>);
  expect(screen.getByRole("banner")).toBeVisible();
  expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Menu" }));
  expect(screen.getByRole("button", { name: "Close menu" })).toHaveAttribute("aria-expanded", "true");
});
```

- [ ] **Step 2: Verify RED**

Run: `cd web && npm test -- --run src/components/app-shell.test.tsx`
Expected: FAIL because the existing shell uses an aside and its menu button is named `Menu`/`Close`.

- [ ] **Step 3: Implement the shared primitives and shell**

```tsx
export function PageIntro({ eyebrow, title, description, actions }: PageIntroProps) {
  return <header className="pageIntro"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p>{actions}</header>;
}

export function DocsFrame({ index, outline, children }: DocsFrameProps) {
  return <div className="docsFrame"><nav aria-label="Section index">{index}</nav><article>{children}</article><aside aria-label="On this page">{outline}</aside></div>;
}
```

Replace the fixed rail with `<header className="siteHeader">`, the wordmark, desktop links, service status, and an accessible mobile sheet. `SignalField` renders decorative spans under `aria-hidden="true"`.

- [ ] **Step 4: Verify GREEN and regression scope**

Run: `cd web && npm test -- --run src/components/app-shell.test.tsx src/components/service-status.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/app-shell.test.tsx web/src/components/app-shell.tsx web/src/components/page-intro.tsx web/src/components/docs-frame.tsx web/src/components/signal-field.tsx web/src/app/layout.tsx web/src/app/globals.css
git commit -m "feat: establish signal studio web shell"
```

### Task 2: Landing-page product narrative

**Files:**
- Create: `web/src/components/analysis-trace.test.tsx`
- Create: `web/src/components/analysis-trace.tsx`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: `DEFAULT_DEMO_MESSAGE`, static masked evidence copy, `SignalField`, and existing `/analyze` and `/guide` routes.
- Produces: `AnalysisTrace`, a non-interactive product illustration with an explicit link to the real analyzer.

- [ ] **Step 1: Write the failing trace test**

```tsx
it("shows input, masked evidence, and human-review output", () => {
  render(<AnalysisTrace />);
  expect(screen.getByText(/synthetic message/i)).toBeVisible();
  expect(screen.getByText(/masked signals/i)).toBeVisible();
  expect(screen.getByText(/human review/i)).toBeVisible();
  expect(screen.getByRole("link", { name: /open live analyzer/i })).toHaveAttribute("href", "/analyze");
});
```

- [ ] **Step 2: Verify RED**

Run: `cd web && npm test -- --run src/components/analysis-trace.test.tsx`
Expected: FAIL because `AnalysisTrace` does not exist.

- [ ] **Step 3: Build the landing composition**

Implement the centered hero, `SignalField`, real-data trace, capability mosaic, honest candidate/runtime boundary, and final professor evaluation call to action. Keep the exact 75.0%, 50.0%, 87.5%, 64-row, and eight-test-row claims sourced from committed research data where possible.

- [ ] **Step 4: Verify GREEN**

Run: `cd web && npm test -- --run src/components/analysis-trace.test.tsx src/components/service-status.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/analysis-trace.test.tsx web/src/components/analysis-trace.tsx web/src/app/page.tsx web/src/app/globals.css
git commit -m "feat: turn landing page into product evidence"
```

### Task 3: Analysis workspace and result hierarchy

**Files:**
- Modify: `web/src/app/analyze/page.tsx`
- Modify: `web/src/components/analysis-workbench.test.tsx`
- Modify: `web/src/components/analysis-workbench.tsx`
- Modify: `web/src/components/analysis-result.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: existing `/api/analyze`, `/api/analyze-image`, `AnalysisResult`, prepared examples, and storage state.
- Produces: a single-column pre-analysis layout and a two-column `analysisWorkspaceHasResult` layout after successful analysis.

- [ ] **Step 1: Write the failing result-layout test**

```tsx
it("moves the completed result beside the evidence input", async () => {
  render(<AnalysisWorkbench />);
  await userEvent.click(screen.getByRole("button", { name: "Analyze message" }));
  expect(await screen.findByTestId("analysis-workspace")).toHaveAttribute("data-state", "complete");
  expect(screen.getByRole("heading", { name: /review decision/i })).toBeVisible();
});
```

- [ ] **Step 2: Verify RED**

Run: `cd web && npm test -- --run src/components/analysis-workbench.test.tsx`
Expected: FAIL because the workspace has no state attribute and the result heading uses the old hierarchy.

- [ ] **Step 3: Implement the new composition**

Wrap intake and result in `data-testid="analysis-workspace"`, set `data-state`, keep all fetch/error logic unchanged, reduce nested surfaces, and order decision, evidence, explanation, OCR provenance, and complaint draft according to the spec.

- [ ] **Step 4: Verify GREEN**

Run: `cd web && npm test -- --run src/components/analysis-workbench.test.tsx src/components/analysis-result.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/app/analyze/page.tsx web/src/components/analysis-workbench.test.tsx web/src/components/analysis-workbench.tsx web/src/components/analysis-result.tsx web/src/app/globals.css
git commit -m "feat: redesign live evidence workspace"
```

### Task 4: Relationship signal map

**Files:**
- Modify: `web/src/app/relationships/page.tsx`
- Modify: `web/src/components/relationship-workbench.test.tsx`
- Modify: `web/src/components/relationship-workbench.tsx`
- Modify: `web/src/components/relationship-graph.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: existing synthetic seed/reset functions and `EntityGraph.edges`.
- Produces: a responsive signal-map page with metrics before the graph and the edge-truth table after it.

- [ ] **Step 1: Write the failing order test**

```tsx
it("places bounded metrics before the visual graph", () => {
  render(<RelationshipWorkbench initialGraph={graphFixture} />);
  const metrics = screen.getByRole("region", { name: "Bounded cluster metrics" });
  const graph = screen.getByRole("region", { name: "Relationship signal map" });
  expect(metrics.compareDocumentPosition(graph) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});
```

- [ ] **Step 2: Verify RED**

Run: `cd web && npm test -- --run src/components/relationship-workbench.test.tsx`
Expected: FAIL because metrics currently render after the graph and the graph has no named region.

- [ ] **Step 3: Implement the signal-map hierarchy**

Use `PageIntro`, move metrics above the graph, add the named graph region, keep reset visually separate, and preserve edge-derived case/entity rows.

- [ ] **Step 4: Verify GREEN**

Run: `cd web && npm test -- --run src/components/relationship-workbench.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/app/relationships/page.tsx web/src/components/relationship-workbench.test.tsx web/src/components/relationship-workbench.tsx web/src/components/relationship-graph.tsx web/src/app/globals.css
git commit -m "feat: present relationship evidence as a signal map"
```

### Task 5: Research and run-guide documentation frames

**Files:**
- Create: `web/src/components/docs-frame.test.tsx`
- Modify: `web/src/app/research/page.tsx`
- Modify: `web/src/app/guide/page.tsx`
- Modify: `web/src/components/research-evidence.tsx`
- Modify: `web/src/components/professor-guide.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: `DocsFrame`, existing research snapshot, model tables, commands, and safety copy.
- Produces: anchored section IDs, left section indexes, and right on-page outlines for both long-form pages.

- [ ] **Step 1: Write the failing frame test**

```tsx
it("links the section index and outline to real content headings", () => {
  render(<DocsFrame index={[{ href: "#models", label: "Models" }]} outline={[{ href: "#models", label: "Models" }]}><h2 id="models">Models</h2></DocsFrame>);
  expect(screen.getByRole("navigation", { name: "Section index" })).toContainElement(screen.getByRole("link", { name: "Models" }));
  expect(screen.getByRole("complementary", { name: "On this page" })).toBeVisible();
});
```

- [ ] **Step 2: Verify RED**

Run: `cd web && npm test -- --run src/components/docs-frame.test.tsx`
Expected: FAIL until `DocsFrame` accepts typed link collections and renders semantic links.

- [ ] **Step 3: Implement anchored documentation layouts**

Add stable IDs for comparison, approaches, parameters, hosted run, Docker run, development, verification, and failure states. Preserve table captions and every metric/source boundary.

- [ ] **Step 4: Verify GREEN**

Run: `cd web && npm test -- --run src/components/docs-frame.test.tsx src/components/research-evidence.test.tsx src/components/professor-guide.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/docs-frame.test.tsx web/src/components/docs-frame.tsx web/src/app/research/page.tsx web/src/app/guide/page.tsx web/src/components/research-evidence.tsx web/src/components/professor-guide.tsx web/src/app/globals.css
git commit -m "feat: add research and run documentation frames"
```

### Task 6: Browser verification, responsive polish, and visual evidence

**Files:**
- Modify: `web/e2e/professor-flow.spec.ts`
- Modify: `web/src/app/globals.css`
- Create locally only: `output/playwright/fraudlens-*-after.png`

**Interfaces:**
- Consumes: all redesigned routes and existing mocked professor flows.
- Produces: browser evidence for navigation, responsive behavior, reduced motion, accessibility, and screenshots.

- [ ] **Step 1: Add failing browser expectations**

```ts
await page.goto("/");
await expect(page.getByRole("banner")).toBeVisible();
await expect(page.getByRole("region", { name: "Synthetic analysis trace" })).toBeVisible();
await page.emulateMedia({ reducedMotion: "reduce" });
await expect(page.locator(".signalField")).toHaveCSS("animation-duration", "0.01ms");
```

- [ ] **Step 2: Verify RED**

Run: `cd web && npx playwright test e2e/professor-flow.spec.ts --project=chromium`
Expected: FAIL on the new Signal Studio-specific structure or motion assertion.

- [ ] **Step 3: Finish responsive CSS and repair browser regressions**

Check 1440, 1024, 768, and 390 pixel widths; remove horizontal overflow; keep tables scrollable; preserve focus; and ensure the mobile sheet closes after navigation.

- [ ] **Step 4: Run complete verification**

Run: `cd web && npm test -- --run && npm run lint && npm run typecheck && npm run build && npx playwright test`
Expected: all commands exit 0.

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: all Python tests pass because backend behavior remains unchanged.

- [ ] **Step 5: Capture final screenshots**

Run Playwright full-page screenshots for `/`, `/analyze`, `/relationships`, `/research`, and `/guide` at 1440 by 1000. Store them under ignored `output/playwright/` for the user review.

- [ ] **Step 6: Commit**

```bash
git add web/e2e/professor-flow.spec.ts web/src/app/globals.css
git commit -m "test: verify signal studio professor flows"
```
