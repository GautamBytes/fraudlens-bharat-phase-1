# Recorded Evidence Tour Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a three-step recorded product walkthrough to the landing page and refine Analyze, Relationships, Research, and Run Guide into one cohesive investigation interface.

**Architecture:** Keep all request, model, OCR, graph, and research data flows unchanged. Add one static `RecordedDemoTour` component, presentation-only cues within existing workbenches, and a standalone Playwright capture script that replays deterministic synthetic fixtures into the real UI before writing committed showcase images.

**Tech Stack:** Next.js 16, React 19, TypeScript, Vitest, Testing Library, Playwright, CSS, static PNG assets.

## Global Constraints

- Preserve the dark Signal Studio visual system and current API contracts.
- Use only synthetic evidence and masked identifiers in committed screenshots.
- Label every showcase story “Recorded synthetic demonstration.”
- Do not describe replayed screenshots as live requests or production benchmarks.
- Preserve exact research metrics, model roles, dataset counts, and limitations.
- Preserve storage-off defaults, OCR limits, graph semantics, and human-review boundaries.
- Support 1440px, 768px, and 390px without horizontal page overflow.

---

### Task 1: Recorded landing-page walkthrough

**Files:**
- Create: `web/src/components/recorded-demo-tour.tsx`
- Create: `web/src/components/recorded-demo-tour.test.tsx`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Produces: `RecordedDemoTour(): JSX.Element` with three ordered `RecordedDemoStory` sections.
- Consumes: `/showcase/text-analysis.png`, `/showcase/screenshot-analysis.png`, and `/showcase/relationship-graph.png`.

- [ ] **Step 1: Write the failing component test**

```tsx
render(<RecordedDemoTour />);
expect(screen.getByRole("heading", { name: "See the system before you run it." })).toBeVisible();
expect(screen.getAllByText("Recorded synthetic demonstration")).toHaveLength(3);
expect(screen.getByRole("img", { name: /completed text analysis/i })).toHaveAttribute("src", "/showcase/text-analysis.png");
expect(screen.getByRole("img", { name: /completed screenshot analysis/i })).toHaveAttribute("src", "/showcase/screenshot-analysis.png");
expect(screen.getByRole("img", { name: /two synthetic reports linked/i })).toHaveAttribute("src", "/showcase/relationship-graph.png");
expect(screen.getAllByRole("link", { name: /open/i })).toHaveLength(3);
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd web && npm test -- --run src/components/recorded-demo-tour.test.tsx`

Expected: FAIL because `RecordedDemoTour` does not exist.

- [ ] **Step 3: Implement the ordered story component**

```tsx
const STORIES = [
  { step: "01", title: "Classify a suspicious message", image: "/showcase/text-analysis.png", href: "/analyze" },
  { step: "02", title: "Extract evidence from a screenshot", image: "/showcase/screenshot-analysis.png", href: "/analyze" },
  { step: "03", title: "Connect repeated masked signals", image: "/showcase/relationship-graph.png", href: "/relationships" },
] as const;
```

Render an accessible section headed “See the system before you run it.” Each story includes the fixed synthetic label, a descriptive image, input/output/inspection copy, and a direct link. Render `<RecordedDemoTour />` between the landing-page capability mosaic and research boundary. Add alternating desktop and stacked mobile styles.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `cd web && npm test -- --run src/components/recorded-demo-tour.test.tsx`

Expected: PASS.

### Task 2: Refine all four inner workspaces

**Files:**
- Modify: `web/src/components/analysis-workbench.tsx`
- Modify: `web/src/components/analysis-workbench.test.tsx`
- Modify: `web/src/components/relationship-workbench.tsx`
- Modify: `web/src/components/relationship-workbench.test.tsx`
- Modify: `web/src/components/research-evidence.tsx`
- Modify: `web/src/components/research-evidence.test.tsx`
- Modify: `web/src/components/professor-guide.tsx`
- Modify: `web/src/components/professor-guide.test.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- `AnalysisWorkbench` adds a presentation-only ready-state guide headed `What happens next`.
- `RelationshipWorkbench` adds an ordered `Build → Inspect → Verify` cue without changing handlers.
- `ResearchEvidence` adds `aria-label="Research metric signal"` bars derived from existing model values.
- `ProfessorGuide` adds `aria-label="Evaluation paths"` anchor navigation.

- [ ] **Step 1: Write failing structural tests**

```tsx
render(<AnalysisWorkbench />);
expect(screen.getByRole("heading", { name: "What happens next" })).toBeVisible();

render(<RelationshipWorkbench initialGraph={null} />);
expect(screen.getByRole("list", { name: "Relationship walkthrough" })).toHaveTextContent("BuildInspectVerify");

render(<ResearchEvidence />);
expect(screen.getByRole("region", { name: "Research metric signal" })).toHaveTextContent("AccuracyMacro-F1Coverage");

render(<ProfessorGuide />);
expect(screen.getByRole("navigation", { name: "Evaluation paths" })).toHaveTextContent("HostedDockerDevelopment");
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `cd web && npm test -- --run src/components/analysis-workbench.test.tsx src/components/relationship-workbench.test.tsx src/components/research-evidence.test.tsx src/components/professor-guide.test.tsx`

Expected: FAIL on all four missing structures.

- [ ] **Step 3: Add presentation-only structures**

Add a three-item ready-state guide beside the Analyze intake; hide it once a result exists. Add a labelled ordered cue inside Relationships above the graph. Build research bars from `candidate` and `deployed` numeric values and keep the exact table below. Add three guide path anchors for `#hosted`, `#docker-run`, and `#development`. Style these elements with shared dark panels, monospace step labels, and responsive stacking.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `cd web && npm test -- --run src/components/analysis-workbench.test.tsx src/components/relationship-workbench.test.tsx src/components/research-evidence.test.tsx src/components/professor-guide.test.tsx`

Expected: all focused tests pass with existing behavioral assertions unchanged.

### Task 3: Reproducible showcase capture and committed assets

**Files:**
- Create: `web/scripts/capture-showcase.mjs`
- Create: `web/src/components/showcase-assets.test.ts`
- Create: `web/public/showcase/text-analysis.png`
- Create: `web/public/showcase/screenshot-analysis.png`
- Create: `web/public/showcase/relationship-graph.png`
- Modify: `web/package.json`

**Interfaces:**
- Produces: `npm run capture:showcase`, requiring an existing website at `SHOWCASE_BASE_URL` or `http://127.0.0.1:3000`.
- Writes: the three stable PNG paths consumed by `RecordedDemoTour`.

- [ ] **Step 1: Write the failing asset contract test**

```ts
for (const name of ["text-analysis.png", "screenshot-analysis.png", "relationship-graph.png"]) {
  const asset = resolve(process.cwd(), "public", "showcase", name);
  expect(existsSync(asset)).toBe(true);
  expect(statSync(asset).size).toBeGreaterThan(10_000);
}
```

- [ ] **Step 2: Run the asset test and verify RED**

Run: `cd web && npm test -- --run src/components/showcase-assets.test.ts`

Expected: FAIL because the images do not exist.

- [ ] **Step 3: Implement deterministic capture**

Create a Playwright script that launches Chromium at 1440×1000, intercepts analysis and graph routes with the existing synthetic KYC result, an OCR variant with `input_source: "image"`, and a two-case masked graph. For text and screenshot stories, drive the real controls and capture `data-testid="analysis-workspace"`; for relationships, click `Build synthetic link` and capture `.relationshipStack`. Write PNGs to `public/showcase`. Add `"capture:showcase": "node scripts/capture-showcase.mjs"` to `package.json`.

- [ ] **Step 4: Generate assets and verify GREEN**

Run the website on port 3000, then run: `cd web && npm run capture:showcase && npm test -- --run src/components/showcase-assets.test.ts`

Expected: three PNGs are written and the asset test passes.

### Task 4: Final browser verification and delivery

**Files:**
- Verify every modified source, test, script, and image.

- [ ] **Step 1: Run complete frontend verification**

```bash
cd web
npm test -- --run
npm run lint
npm run build
npm run typecheck
npx playwright test
```

Expected: all unit tests, lint, production build, TypeScript, professor journeys, responsive checks, and axe scans pass.

- [ ] **Step 2: Inspect desktop and mobile pages**

Capture full-page screenshots of `/`, `/analyze`, `/relationships`, `/research`, and `/guide` at 1440×1000 plus `/` and `/analyze` at 390×844. Verify screenshot legibility, footer placement, no horizontal overflow, and consistent dark surfaces.

- [ ] **Step 3: Review, commit, and push**

Stage only the specification/plan, website source/tests, capture script, package metadata, and `web/public/showcase/` assets. Do not stage `.playwright-cli/`, `output/`, `.next/`, or generated `next-env.d.ts` changes.

```bash
git commit -m "feat: add recorded evidence walkthrough"
git push
```
