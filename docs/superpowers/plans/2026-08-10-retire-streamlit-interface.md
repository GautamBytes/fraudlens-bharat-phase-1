# Retire the Streamlit Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove Streamlit and its legacy adapters from the active FraudLens Bharat product so Next.js and FastAPI are the only supported interfaces.

**Architecture:** Delete the Streamlit-only UI boundary while preserving the shared analysis, OCR, persistence, graph, and privacy services used by FastAPI. Enforce the new boundary with repository contract tests, regenerate dependency locks and presentation evidence, and retain only explicitly historical references to the retired Phase 1 interface.

**Tech Stack:** Python 3.10+, FastAPI, Next.js 16, universal hashed pip locks, Docker Compose, pytest, Vitest, Playwright, PowerPoint Open XML.

## Global Constraints

- Do not change FastAPI endpoint or response contracts.
- Do not change model artifacts, training data, or evaluation metrics.
- Do not add a replacement Python UI framework.
- Keep truthful Phase 1 history, but label the Streamlit interface retired.
- Do not retain executable Streamlit commands or current-support claims.
- Preserve container hardening, OCR packages, health checks, and loopback defaults.
- Use test-first RED/GREEN cycles before deleting production files.
- Do not stage local `.playwright-cli/` or `output/` artifacts.

---

### Task 1: Remove the Legacy Runtime and Dependency Surface

**Files:**
- Create: `tests/test_streamlit_retirement.py`
- Delete: `src/fraudlens/dashboard.py`
- Delete: `src/fraudlens/dashboard_workflow.py`
- Delete: `src/fraudlens/graph_dashboard.py`
- Delete: `tests/test_dashboard_workflow.py`
- Delete: `tests/test_graph_dashboard.py`
- Delete: `tests/test_client_integration.py`
- Modify: `tests/test_demo_evidence.py`
- Modify: `tests/test_dependency_security.py`
- Modify: `src/fraudlens/analysis_service.py`
- Modify: `requirements.txt`
- Regenerate: `requirements.lock`
- Regenerate: `requirements-runtime.lock`
- Modify: `Dockerfile`

**Interfaces:**
- Consumes: the existing FastAPI/shared-service runtime and universal lock workflow.
- Produces: a Python runtime with no Streamlit import, module, pin, or container setting.

- [ ] **Step 1: Add a failing active-runtime retirement contract**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_is_absent_from_the_active_runtime():
    for relative_path in (
        "src/fraudlens/dashboard.py",
        "src/fraudlens/dashboard_workflow.py",
        "src/fraudlens/graph_dashboard.py",
    ):
        assert not (ROOT / relative_path).exists(), relative_path

    for relative_path in (
        "requirements.txt",
        "requirements.lock",
        "requirements-runtime.lock",
        "Dockerfile",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8").lower()
        assert "streamlit" not in text, relative_path

    for source in (ROOT / "src" / "fraudlens").glob("*.py"):
        assert "streamlit" not in source.read_text(encoding="utf-8").lower(), source
```

- [ ] **Step 2: Run the contract and verify RED**

Run: `PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest tests/test_streamlit_retirement.py -q`

Expected: FAIL because all three legacy modules and Streamlit dependency/configuration still exist.

- [ ] **Step 3: Delete the Streamlit-only source and test files**

Delete the six files listed above with `apply_patch`. In `tests/test_demo_evidence.py`, remove the `dashboard` import and the two dashboard catalog/scope tests while retaining generator, graph, screenshot, and deterministic-evidence tests. In `tests/test_client_integration.py`, preserve the generator assertion by moving it into `tests/test_demo_evidence.py` before deleting the file:

```python
def test_demo_case_generation_uses_service_without_persisting_cases():
    source = (ROOT / "src" / "fraudlens" / "generate_demo_cases.py").read_text(
        encoding="utf-8"
    )
    assert "from fraudlens.api" not in source
    assert "create_analysis_service" in source
    assert "AnalysisInput(text=text, store_case=False)" in source
```

- [ ] **Step 4: Remove Streamlit from direct runtime requirements and Docker**

Delete `streamlit==1.54.0` from `requirements.txt`. Delete `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` from the Docker `ENV` block. Rewrite the compatibility-caller comment in `analysis_service.py` so it describes only direct shared-service callers and does not mention dashboards.

- [ ] **Step 5: Regenerate both universal hashed lockfiles**

Run:

```bash
uv pip compile requirements.txt requirements-dev.txt --python-version 3.10 --universal --generate-hashes -o requirements.lock
uv pip compile requirements.txt --python-version 3.11 --universal --generate-hashes -o requirements-runtime.lock
```

Expected: both commands exit 0; neither lock contains `streamlit`; platform-conditional `greenlet` remains pinned and hashed.

- [ ] **Step 6: Update security assertions for the supported runtime**

In `tests/test_dependency_security.py`, remove `streamlit==1.54.0` from the expected direct dependencies. Preserve the FastAPI, multipart, Pillow, Python-version, universal-hash, least-privilege CI, reproducible-artifact, and `greenlet` assertions.

- [ ] **Step 7: Run the runtime contract and focused shared-service tests GREEN**

Run:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest -q tests/test_streamlit_retirement.py tests/test_demo_evidence.py tests/test_dependency_security.py tests/test_api.py tests/test_image_analysis.py tests/test_graph_analysis.py tests/test_database_privacy.py tests/test_container_contract.py
```

Expected: all collected focused tests pass and import collection finds no deleted dashboard module.

- [ ] **Step 8: Audit the regenerated dependency surface**

Run:

```bash
uvx pip-audit -r requirements.lock
uvx pip-audit -r requirements-runtime.lock
```

Expected: both audits report no known vulnerabilities.

- [ ] **Step 9: Commit the runtime retirement**

```bash
git add requirements.txt requirements.lock requirements-runtime.lock Dockerfile src/fraudlens tests
git commit -m "refactor: remove legacy Streamlit runtime"
```

---

### Task 2: Make Documentation and Generated Evidence Next.js/FastAPI-only

**Files:**
- Modify: `tests/test_streamlit_retirement.py`
- Modify: `tests/test_dependency_security.py`
- Modify: `README.md`
- Modify: `docs/installation_guide.md`
- Modify: `docs/user_manual.md`
- Modify: `docs/professor_testing_guide.md`
- Modify: `docs/deployment_guide.md`
- Modify: `docs/test_cases.md`
- Modify: `docs/release_checklist.md`
- Modify: `docs/final_capstone_report.md`
- Modify: `docs/phase2_research_report.md`
- Modify: `docs/literature_review.md`
- Modify: `docs/comparative_analysis.md`
- Modify: `docs/evaluation_plan.md`
- Modify: `docs/presentation/demo_video_runbook.md`
- Modify: `docs/weekly_progress.md`
- Modify: `docs/phase1_report.md`
- Modify: `outputs/screenshots/README.md`
- Modify: `src/fraudlens/presentation_evidence.py`
- Regenerate: `outputs/presentation/final_system_architecture.png`
- Verify unchanged metrics: `outputs/presentation/final_evidence.json`

**Interfaces:**
- Consumes: the Next.js routes `/`, `/analyze`, `/relationships`, `/research`, `/guide` and FastAPI endpoints.
- Produces: current operational documentation and architecture evidence with no active Streamlit/dashboard claim.

- [ ] **Step 1: Extend the retirement contract for active documentation**

```python
ACTIVE_DOCUMENTS = (
    "README.md",
    "docs/installation_guide.md",
    "docs/user_manual.md",
    "docs/professor_testing_guide.md",
    "docs/deployment_guide.md",
    "docs/test_cases.md",
    "docs/release_checklist.md",
    "docs/final_capstone_report.md",
    "docs/phase2_research_report.md",
    "docs/literature_review.md",
    "docs/comparative_analysis.md",
    "docs/evaluation_plan.md",
    "docs/presentation/demo_video_runbook.md",
    "outputs/screenshots/README.md",
)


def test_active_documentation_supports_only_nextjs_and_fastapi():
    for relative_path in ACTIVE_DOCUMENTS:
        text = (ROOT / relative_path).read_text(encoding="utf-8").lower()
        assert "streamlit" not in text, relative_path
        assert "streamlit run" not in text, relative_path
        assert "legacy streamlit dashboard retained" not in text, relative_path

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "modern Next.js professor website" in readme
    assert "FastAPI backend" in readme
```

- [ ] **Step 2: Run the documentation contract and verify RED**

Run: `PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest tests/test_streamlit_retirement.py::test_active_documentation_supports_only_nextjs_and_fastapi -q`

Expected: FAIL on README and current operational/report files.

- [ ] **Step 3: Rewrite active run and workflow guidance**

Apply these content rules across the listed active documents:

```text
Current interfaces: Next.js website + FastAPI API
Hosted professor path: open the Vercel website
Complete local path: docker compose up --build --detach, then open http://127.0.0.1:3000
API-only path: uvicorn fraudlens.api:app --host 127.0.0.1 --port 8000
Text analysis: /analyze message tab or POST /analyze
Screenshot analysis: /analyze screenshot tab or POST /analyze-image
Relationship review: /relationships or GET /graph
```

Remove the “Run Dashboard” section, port `8501`, dashboard consent/refresh instructions, and dashboard compatibility claims. Keep storage-off, in-memory image handling, masked graph, human-review, and synthetic-only boundaries.

- [ ] **Step 4: Preserve historical truth with explicit retirement notes**

In `docs/phase1_report.md` and `docs/weekly_progress.md`, historical rows may retain the word Streamlit only if the document also includes this current-scope statement:

```markdown
> Current-scope note (2026-08-10): Phase 1 used a Streamlit demonstration interface. That interface is retired; the supported final product uses the Next.js website and FastAPI.
```

Delete all executable `streamlit run` commands and references to removed dashboard screenshots from historical documents.

- [ ] **Step 5: Update graph/OCR documentation tests for the website**

In `tests/test_dependency_security.py`, rename screenshot and graph contract tests from “dashboard” to “website”. Replace assertions with exact current language:

```python
for expected_text in (
    "website shows masked labels and hides opaque identifiers",
    "does not run the graph query until explicit Build synthetic link or Refresh",
):
    assert expected_text in documentation
```

Replace the test inventory label `Entity graph dashboard refresh and truncation` with `Entity graph website refresh and truncation` in both the test and `docs/test_cases.md`.

- [ ] **Step 6: Update the generated architecture labels**

In `src/fraudlens/presentation_evidence.py`, make these exact replacements:

```python
box(0.7, 6.6, 2.0, 1.0, "Text input", "Next.js / FastAPI", _BLUE)
box(9.0, 6.0, 2.25, 1.15, "Web + API", "Result + provenance", _BLUE)
```

Run:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3.11 -m fraudlens.presentation_evidence --repo-root . --output outputs/presentation
```

Expected: the architecture PNG changes; `final_evidence.json` remains byte-identical because model/dataset claims did not change.

- [ ] **Step 7: Run documentation and presentation evidence tests GREEN**

Run:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest -q tests/test_streamlit_retirement.py tests/test_dependency_security.py tests/test_release_docs.py tests/test_research_report.py tests/test_presentation_evidence.py tests/test_capstone_package.py
```

Expected: all focused tests pass.

- [ ] **Step 8: Commit documentation and evidence changes**

```bash
git add README.md docs outputs/screenshots/README.md outputs/presentation src/fraudlens/presentation_evidence.py tests/test_dependency_security.py tests/test_streamlit_retirement.py
git commit -m "docs: make Next.js the sole project interface"
```

---

### Task 3: Remove Streamlit from Final Screenshots and PowerPoint

**Files:**
- Modify: `tests/test_demo_evidence.py`
- Modify: `tests/test_capstone_package.py`
- Delete: `outputs/screenshots/dashboard_home.png`
- Delete: `outputs/screenshots/dashboard_analysis_result.png`
- Delete: `outputs/screenshots/dashboard_otp_demo.png`
- Delete: `outputs/screenshots/final_dashboard_home.png`
- Create: `outputs/screenshots/final_web_home.png`
- Modify: `docs/presentation/fraudlens-bharat-final-capstone.pptx`

**Interfaces:**
- Consumes: the current Next.js landing page and existing ten-slide college template.
- Produces: a final screenshot/deck package with no Streamlit visual or text while retaining the existing slide design.

- [ ] **Step 1: Write failing screenshot and deck assertions**

Update the final screenshot inventory in `tests/test_demo_evidence.py`:

```python
expected_names = {
    "final_web_home.png",
    "final_text_analysis.png",
    "final_ocr_analysis.png",
    "final_entity_graph.png",
    "final_api_docs.png",
    "final_api_ready.png",
}
```

Add to `tests/test_capstone_package.py`:

```python
def test_final_deck_describes_only_the_supported_interfaces():
    slide_text = " ".join(_deck_slide_text()).lower()
    assert "streamlit" not in slide_text
    assert "api and dashboard" not in slide_text
    assert "next.js" in slide_text
    assert "fastapi" in slide_text

    with zipfile.ZipFile(DECK) as archive:
        package_text = " ".join(
            archive.read(name).decode("utf-8", errors="ignore").lower()
            for name in archive.namelist()
            if name.endswith(".xml")
        )
    assert "streamlit" not in package_text
```

- [ ] **Step 2: Run focused evidence tests and verify RED**

Run:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest -q tests/test_demo_evidence.py::test_final_demo_screenshots_use_a_consistent_presentation_viewport tests/test_capstone_package.py::test_final_deck_describes_only_the_supported_interfaces
```

Expected: FAIL because `final_web_home.png` is absent and the deck still contains Streamlit/dashboard text.

- [ ] **Step 3: Capture the current website at the presentation viewport**

Start the local web server in one terminal:

```bash
cd web
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Then capture from a second terminal:

```bash
cd web
npx playwright screenshot --color-scheme dark --viewport-size="1600,1200" --wait-for-timeout 800 http://127.0.0.1:3000/ ../outputs/screenshots/final_web_home.png
```

Expected: `final_web_home.png` is RGB PNG at exactly `1600 x 1200` and shows the modern landing page.

- [ ] **Step 4: Delete the four obsolete Streamlit screenshots**

Delete only the four listed files with `apply_patch`. Do not remove current text, OCR, graph, API, research, or website showcase evidence.

- [ ] **Step 5: Unpack and edit the existing deck without changing layout**

Run:

```bash
python /Users/gautammanch/.codex/skills/pptx/scripts/office/unpack.py docs/presentation/fraudlens-bharat-final-capstone.pptx /private/tmp/fraudlens-deck-unpacked
```

Use `apply_patch` on the unpacked XML:

```text
slide3.xml: FastAPI + Streamlit on one analysis service
             -> Next.js + FastAPI on one analysis service
slide7.xml: Storage starts off | Synthetic fixtures only | API and dashboard use the same service
             -> Storage starts off | Synthetic fixtures only | Website and API use the same service
slide6.xml: replace the obsolete typeface token Streamlit with Aptos
```

Clean and repack:

```bash
python /Users/gautammanch/.codex/skills/pptx/scripts/clean.py /private/tmp/fraudlens-deck-unpacked
python /Users/gautammanch/.codex/skills/pptx/scripts/office/pack.py /private/tmp/fraudlens-deck-unpacked /private/tmp/fraudlens-bharat-final-capstone.pptx --original docs/presentation/fraudlens-bharat-final-capstone.pptx
cp /private/tmp/fraudlens-bharat-final-capstone.pptx docs/presentation/fraudlens-bharat-final-capstone.pptx
```

- [ ] **Step 6: Run content and visual QA on the deck**

Run:

```bash
python -m markitdown docs/presentation/fraudlens-bharat-final-capstone.pptx
python /Users/gautammanch/.codex/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf --outdir /private/tmp docs/presentation/fraudlens-bharat-final-capstone.pptx
pdftoppm -jpeg -r 150 /private/tmp/fraudlens-bharat-final-capstone.pdf /private/tmp/fraudlens-slide
```

Inspect slide 3, slide 6, and slide 7 renders for wrapping, overlap, low contrast, and obsolete interface imagery. If any issue appears, fix the affected XML, repack, and render again. Confirm raw package XML contains neither `Streamlit` nor `API and dashboard`.

- [ ] **Step 7: Run screenshot and deck tests GREEN**

Run:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest -q tests/test_demo_evidence.py tests/test_capstone_package.py
```

Expected: all tests pass, including the `1600 x 1200` screenshot and ten-slide deck contracts.

- [ ] **Step 8: Commit the final evidence package**

```bash
git add outputs/screenshots docs/presentation/fraudlens-bharat-final-capstone.pptx tests/test_demo_evidence.py tests/test_capstone_package.py
git commit -m "docs: retire Streamlit presentation evidence"
```

---

### Task 4: Full Verification, Review, and PR Update

**Files:**
- Verify: entire repository
- Modify only if a concrete verification/review failure requires a scoped correction.

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: a merge-ready update to PR #10 with no active Streamlit surface.

- [ ] **Step 1: Prove the retirement contract and scan the repository**

Run:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest -q tests/test_streamlit_retirement.py
rg -n -i "streamlit|streamlit run|api and dashboard" src requirements.txt requirements.lock requirements-runtime.lock Dockerfile README.md docs outputs/screenshots/README.md
```

Expected: the contract passes. `rg` returns only approved historical/spec/plan references that explicitly say the interface is retired.

- [ ] **Step 2: Run the complete Python suite**

Run: `PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest -q`

Expected: all collected tests pass; the count may decrease only by the number of deleted Streamlit-only tests. Dynamic presentation claims continue to require the current collected count to be at least the frozen release snapshot.

- [ ] **Step 3: Run the complete website verification**

Run:

```bash
cd web
npm test -- --run
npm run lint
npm run typecheck
npm run build
npx playwright test
```

Expected: unit, lint, typecheck, build, browser flows, responsive checks, and automated accessibility checks all pass.

- [ ] **Step 4: Verify dependencies and container configuration**

Run:

```bash
uvx pip-audit -r requirements.lock
uvx pip-audit -r requirements-runtime.lock
docker compose config --quiet
git diff --check
```

Expected: no known vulnerabilities, valid Compose configuration, and no whitespace errors.

- [ ] **Step 5: Request a strict final code/document/deck review**

Reviewer brief:

```text
Review the Streamlit retirement against docs/superpowers/specs/2026-08-10-retire-streamlit-interface-design.md. Check that active code, dependencies, locks, containers, operational docs, screenshots, generated architecture evidence, and the final PPT contain no Streamlit support; historical Phase 1 mentions must be truthful and explicitly retired. Confirm FastAPI/Next.js parity and no regression to OCR, privacy, graph, API, research, deployment, or accessibility behavior. Return Critical/Important/Minor findings and READY/NOT READY.
```

- [ ] **Step 6: Fix every Critical/Important finding with a RED/GREEN regression**

For each valid issue, add the smallest failing contract test, verify RED, implement the correction, and rerun the affected suite plus the complete final verification.

- [ ] **Step 7: Push the reviewed branch and monitor both CI runs**

```bash
git push
gh pr checks 10 --watch --interval 10
```

Expected: Python 3.10/3.11.15/3.12, web, and hardened container-smoke jobs all pass for both push and pull-request runs.
