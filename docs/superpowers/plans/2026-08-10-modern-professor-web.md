# Modern Professor Web Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a modern Next.js professor evaluation website on Vercel backed by the real authenticated FraudLens FastAPI/OCR container, with complete hosted and local run guidance.

**Architecture:** A Next.js 16 application in `web/` renders the professor workbench and uses same-origin route handlers to proxy bounded requests to FastAPI. FastAPI optionally requires a constant-time checked demo key for all data routes, while health/readiness remain non-sensitive. The existing Docker application remains the local and offline fallback.

**Tech Stack:** Next.js 16.3.0, React 19.2.8, TypeScript 5.9.3, CSS modules/global tokens, Vitest 4.1.10, Testing Library 16.3.2, Playwright 1.62.1, FastAPI, pytest, Docker, Vercel, Render.

## Global Constraints

- Browser uploads are capped at 4,000,000 bytes; the direct Python API remains capped at 5 MiB.
- The browser never receives `FRAUDLENS_API_URL` or `FRAUDLENS_DEMO_API_KEY`.
- Case storage defaults to false and hosted pages request synthetic data only.
- Screenshot bytes are never retained.
- The deployed runtime and research candidate metrics remain separate.
- No presentation script is added to the repository.
- The professor guide covers hosted evaluation, Docker Compose, split development, verification, reset, and failure-safe operation.

---

### Task 1: Optional hosted-demo API authentication

**Files:**
- Modify: `src/fraudlens/settings.py`
- Modify: `src/fraudlens/api.py`
- Modify: `.env.example`
- Test: `tests/test_api.py`
- Test: `tests/test_settings.py`

**Interfaces:**
- Consumes: existing `Settings.from_env()` and FastAPI request middleware.
- Produces: `Settings.demo_api_key: Optional[str]`; header `X-FraudLens-Demo-Key`; public `/health` and `/ready`.

- [ ] **Step 1: Write failing settings and API tests**

```python
def test_demo_api_key_is_optional_and_hidden_from_repr():
    settings = Settings.from_env({"FRAUDLENS_ENVIRONMENT": "test"})
    assert settings.demo_api_key is None
    secured = Settings.from_env({
        "FRAUDLENS_ENVIRONMENT": "test",
        "FRAUDLENS_DEMO_API_KEY": "correct-horse-battery-staple-with-entropy",
    })
    assert secured.demo_api_key is not None
    assert secured.demo_api_key not in repr(secured)

def test_demo_key_protects_data_routes_but_not_readiness(tmp_path):
    client = build_test_client(tmp_path, demo_api_key="correct-horse-battery-staple-with-entropy")
    assert client.get("/ready").status_code == 200
    assert client.post("/analyze", json={"text": "fake kyc"}).status_code == 401
    response = client.post(
        "/analyze",
        headers={"X-FraudLens-Demo-Key": "correct-horse-battery-staple-with-entropy"},
        json={"text": "fake kyc"},
    )
    assert response.status_code == 200
```

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=src python3.11 -m pytest -q tests/test_settings.py tests/test_api.py`

Expected: FAIL because `demo_api_key` and middleware do not exist.

- [ ] **Step 3: Implement the minimal boundary**

```python
from dataclasses import dataclass, field
from secrets import compare_digest

demo_api_key: Optional[str] = field(default=None, repr=False)

configured_demo_key = values.get("FRAUDLENS_DEMO_API_KEY")
demo_api_key = configured_demo_key.strip() if configured_demo_key else None
if demo_api_key is not None and not _is_strong_production_secret(demo_api_key):
    raise ValueError("FRAUDLENS_DEMO_API_KEY must be a strong secret when set")

@application.middleware("http")
async def authenticate_hosted_demo(request: Request, call_next):
    expected = resolved_settings.demo_api_key
    if expected and request.url.path not in {"/health", "/ready"}:
        supplied = request.headers.get("X-FraudLens-Demo-Key", "")
        if not compare_digest(supplied, expected):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)
```

- [ ] **Step 4: Run GREEN and full Python tests**

Run: `PYTHONPATH=src python3.11 -m pytest -q tests/test_settings.py tests/test_api.py`

Expected: PASS.

Run: `MPLCONFIGDIR=/tmp/fraudlens-matplotlib PYTHONPATH=src python3.11 -m pytest -q`

Expected: 379 or more tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/fraudlens/settings.py src/fraudlens/api.py .env.example tests/test_settings.py tests/test_api.py
git commit -m "security: protect hosted demo API"
```

### Task 2: Next.js foundation and typed proxy

**Files:**
- Create: `web/package.json`
- Create: `web/package-lock.json`
- Create: `web/tsconfig.json`
- Create: `web/next.config.ts`
- Create: `web/eslint.config.mjs`
- Create: `web/vitest.config.ts`
- Create: `web/src/lib/contracts.ts`
- Create: `web/src/lib/server/fraudlens.ts`
- Create: `web/src/app/api/health/route.ts`
- Create: `web/src/app/api/analyze/route.ts`
- Create: `web/src/app/api/analyze-image/route.ts`
- Create: `web/src/app/api/graph/route.ts`
- Create: `web/src/app/api/cases/route.ts`
- Test: `web/src/lib/server/fraudlens.test.ts`

**Interfaces:**
- Consumes: FastAPI `/health`, `/ready`, `/analyze`, `/analyze-image`, `/graph`, and `/cases` contracts.
- Produces: `fraudlensRequest(path, init, timeoutMs)` and same-origin `/api/*` endpoints.

- [ ] **Step 1: Write the failing proxy tests**

```ts
it("keeps the backend URL and demo key server-side", async () => {
  process.env.FRAUDLENS_API_URL = "https://api.example.test";
  process.env.FRAUDLENS_DEMO_API_KEY = "secret";
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 200 })));
  await fraudlensRequest("/analyze", { method: "POST", body: "{}" });
  expect(fetch).toHaveBeenCalledWith(
    "https://api.example.test/analyze",
    expect.objectContaining({ headers: expect.objectContaining({ "X-FraudLens-Demo-Key": "secret" }) }),
  );
});

it("rejects image bodies above 4,000,000 bytes", async () => {
  const request = new Request("http://localhost/api/analyze-image", {
    method: "POST",
    headers: { "content-type": "image/png", "content-length": "4000001" },
    body: new Uint8Array(1),
  });
  expect((await POST(request)).status).toBe(413);
});
```

- [ ] **Step 2: Run RED**

Run: `cd web && npm test -- --run`

Expected: FAIL because the web application and proxy do not exist.

- [ ] **Step 3: Implement package, contracts, and proxy**

```ts
export async function fraudlensRequest(path: string, init: RequestInit = {}, timeoutMs = 65_000) {
  const baseUrl = process.env.FRAUDLENS_API_URL;
  if (!baseUrl) return new Response(JSON.stringify({ detail: "Analysis service is not configured" }), { status: 503 });
  const headers = new Headers(init.headers);
  const key = process.env.FRAUDLENS_DEMO_API_KEY;
  if (key) headers.set("X-FraudLens-Demo-Key", key);
  const response = await fetch(new URL(path, baseUrl), {
    ...init,
    headers,
    cache: "no-store",
    signal: AbortSignal.timeout(timeoutMs),
  });
  return new Response(response.body, {
    status: response.status,
    headers: { "content-type": response.headers.get("content-type") ?? "application/json", "cache-control": "no-store" },
  });
}
```

- [ ] **Step 4: Run GREEN, lint, and typecheck**

Run: `cd web && npm test -- --run && npm run lint && npm run typecheck`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat: add typed FraudLens web gateway"
```

### Task 3: Evidence-workbench interface

**Files:**
- Create: `web/src/app/layout.tsx`
- Create: `web/src/app/globals.css`
- Create: `web/src/app/page.tsx`
- Create: `web/src/app/analyze/page.tsx`
- Create: `web/src/components/app-shell.tsx`
- Create: `web/src/components/service-status.tsx`
- Create: `web/src/components/analysis-workbench.tsx`
- Create: `web/src/components/analysis-result.tsx`
- Create: `web/src/components/evidence-rail.tsx`
- Create: `web/src/lib/demo-data.ts`
- Test: `web/src/components/analysis-workbench.test.tsx`
- Test: `web/src/components/analysis-result.test.tsx`

**Interfaces:**
- Consumes: same-origin `/api/health`, `/api/analyze`, and `/api/analyze-image`.
- Produces: responsive Evaluate and Analyze experiences using `AnalysisResult`.

- [ ] **Step 1: Write failing UI tests**

```tsx
it("starts with storage off and analyzes a synthetic example", async () => {
  render(<AnalysisWorkbench />);
  expect(screen.getByRole("checkbox", { name: /store this synthetic analysis/i })).not.toBeChecked();
  await userEvent.click(screen.getByRole("button", { name: /analyze message/i }));
  expect(await screen.findByText(/complaint draft/i)).toBeVisible();
});

it("rejects an oversized screenshot before making a request", async () => {
  render(<AnalysisWorkbench />);
  const file = new File([new Uint8Array(4_000_001)], "large.png", { type: "image/png" });
  await userEvent.upload(screen.getByLabelText(/upload screenshot/i), file);
  expect(screen.getByRole("alert")).toHaveTextContent(/under 4 MB/i);
  expect(fetch).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Run RED**

Run: `cd web && npm test -- --run src/components`

Expected: FAIL because the components do not exist.

- [ ] **Step 3: Implement the workbench and visual system**

```tsx
<main className="workbench">
  <header className="caseHeader">
    <p className="eyebrow">Professor evaluation workspace</p>
    <h1>Trace a suspicious message from raw evidence to a reviewable decision.</h1>
  </header>
  <EvidenceRail activeStep={result ? 4 : pending ? 2 : 1} />
  <AnalysisWorkbench />
</main>
```

Implement CSS variables from the design spec, Sora/Instrument Sans/IBM Plex
Mono via `next/font/google`, visible focus, reduced motion, mobile navigation,
specific loading/error copy, and semantic status regions.

- [ ] **Step 4: Run GREEN and production build**

Run: `cd web && npm test -- --run && npm run lint && npm run typecheck && npm run build`

Expected: PASS and Next.js production build completes.

- [ ] **Step 5: Commit**

```bash
git add web/src
git commit -m "feat: build modern fraud evidence workbench"
```

### Task 4: Relationships, research, and professor guide pages

**Files:**
- Create: `web/src/app/relationships/page.tsx`
- Create: `web/src/app/research/page.tsx`
- Create: `web/src/app/guide/page.tsx`
- Create: `web/src/components/relationship-workbench.tsx`
- Create: `web/src/components/relationship-graph.tsx`
- Create: `web/src/components/research-comparison.tsx`
- Create: `web/src/lib/research-data.ts`
- Test: `web/src/components/relationship-workbench.test.tsx`
- Test: `web/src/lib/research-data.test.ts`

**Interfaces:**
- Consumes: `/api/analyze`, `/api/graph`, `/api/cases`, committed research values.
- Produces: seed/reset relationship demo, deterministic SVG graph, defensible research comparison, in-app guide.

- [ ] **Step 1: Write failing relationship and evidence tests**

```tsx
it("seeds two synthetic incidents and refreshes the masked graph", async () => {
  render(<RelationshipWorkbench />);
  await userEvent.click(screen.getByRole("button", { name: /load synthetic relationship demo/i }));
  expect(await screen.findByText(/2 linked incidents/i)).toBeVisible();
  expect(screen.queryByText(/fraud-demo\.example/)).not.toBeInTheDocument();
});

it("keeps research and deployed metrics separate", () => {
  expect(RESEARCH_CANDIDATE.accuracy).toBe(0.75);
  expect(DEPLOYED_RUNTIME.accuracy).toBe(0.5);
  expect(DATASET_LIMITS.hasLegitimateClass).toBe(false);
});
```

- [ ] **Step 2: Run RED**

Run: `cd web && npm test -- --run src/components/relationship-workbench.test.tsx src/lib/research-data.test.ts`

Expected: FAIL because the graph and research modules do not exist.

- [ ] **Step 3: Implement graph, research, and guide**

```ts
export const RELATIONSHIP_FIXTURES = [
  "Your KYC expires today. Verify at https://fraud-demo.example/kyc now.",
  "Courier held. Pay the release fee at https://fraud-demo.example/release now.",
] as const;

export const RESEARCH_CANDIDATE = { name: "Character TF-IDF", accuracy: 0.75, macroF1: 0.6667, deployed: false } as const;
export const DEPLOYED_RUNTIME = { name: "Calibrated runtime", accuracy: 0.5, macroF1: 0.5, coverage: 0.875, deployed: true } as const;
```

Render graph edges in an accessible SVG with an adjacent textual table. The
guide page must show the hosted sequence, Docker command, split-development
commands, environment variables, verification endpoints, synthetic-only rule,
cold-start behavior, and reset action.

- [ ] **Step 4: Run GREEN and build**

Run: `cd web && npm test -- --run && npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src
git commit -m "feat: add relationship and research evaluation flows"
```

### Task 5: Deployment, CI, and complete run documentation

**Files:**
- Create: `render.yaml`
- Create: `web/vercel.json`
- Create: `web/.env.example`
- Create: `web/playwright.config.ts`
- Create: `web/e2e/professor-flow.spec.ts`
- Create: `docs/professor_testing_guide.md`
- Modify: `README.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/deployment_guide.md`
- Test: `tests/test_deployment.py`

**Interfaces:**
- Consumes: Dockerfile, Next.js build, FastAPI readiness, professor flows.
- Produces: reproducible Vercel/Render configuration and complete hosted/local handoff.

- [ ] **Step 1: Write failing deployment contract tests**

```python
def test_professor_web_deployment_contract_is_documented():
    guide = (ROOT / "docs/professor_testing_guide.md").read_text()
    for phrase in (
        "Hosted professor evaluation",
        "docker compose up --build",
        "FRAUDLENS_API_URL",
        "FRAUDLENS_DEMO_API_KEY",
        "synthetic data only",
        "Reset demo data",
        "/health",
        "/ready",
    ):
        assert phrase in guide
```

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=src python3.11 -m pytest -q tests/test_deployment.py`

Expected: FAIL because the guide and deployment files do not exist.

- [ ] **Step 3: Add deploy configuration, guide, and CI job**

```yaml
services:
  - type: web
    name: fraudlens-api
    runtime: docker
    healthCheckPath: /ready
    envVars:
      - key: FRAUDLENS_ENVIRONMENT
        value: production
      - key: FRAUDLENS_STORE_CASES
        value: "false"
      - key: FRAUDLENS_HMAC_SECRET
        generateValue: true
      - key: FRAUDLENS_DEMO_API_KEY
        generateValue: true
```

Add a web CI job that runs `npm ci`, unit tests, lint, typecheck, build, installs
Chromium, and runs Playwright against mocked same-origin API responses.

- [ ] **Step 4: Verify everything**

Run: `MPLCONFIGDIR=/tmp/fraudlens-matplotlib PYTHONPATH=src python3.11 -m pytest -q`

Run: `cd web && npm ci && npm test -- --run && npm run lint && npm run typecheck && npm run build && npm run test:e2e`

Run: `docker compose config --quiet`

Expected: every command exits zero.

- [ ] **Step 5: Commit and raise the PR**

```bash
git add README.md docs render.yaml web .github/workflows/ci.yml tests/test_deployment.py
git commit -m "deploy: add professor-ready web handoff"
git push -u origin codex/modern-professor-web
```
