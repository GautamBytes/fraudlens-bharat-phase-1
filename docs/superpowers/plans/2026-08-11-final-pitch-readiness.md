# Final Pitch Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce one merge-ready pull request that makes the completed FraudLens Bharat project and its existing ten-slide capstone deck internally consistent, directly accessible to professors, and resilient to one hosted OCR cold-start timeout.

**Architecture:** Keep the current Next.js same-origin BFF and FastAPI analysis service unchanged. Add the retry only at the screenshot-analysis client boundary, keep the release snapshot as the single machine-readable source for presentation test counts, and edit the existing PPTX package without redesigning it.

**Tech Stack:** Python 3.11, pytest, Next.js 14, React, TypeScript, Vitest, Playwright, PowerPoint Open XML, LibreOffice/Poppler rendering tools.

## Global Constraints

- Preserve the existing model artifacts, datasets, metrics, ten-slide layout, screenshots, typography, and research conclusions.
- Retry screenshot analysis exactly once only when the first response is HTTP 504. Do not retry text analysis or any other status.
- Do not expose Render credentials, service URLs, environment secrets, or backend exception details.
- Do not fabricate accuracy, data, supervisor feedback, production claims, or deployment capabilities.
- Do not stage or modify the user-owned `.playwright-cli/` and `output/` directories.
- Use test-driven development for behavioral changes and run fresh verification before claiming completion.

---

## Task 1: Recover Once From a Hosted Screenshot OCR Timeout

**Files:**

- Modify: `web/src/components/analysis-workbench.test.tsx`
- Modify: `web/src/components/analysis-workbench.tsx`

- [ ] Add a component test that uploads a valid PNG, receives HTTP 504 from the first `/api/analyze-image` call, receives a successful analysis result from the second call, and asserts that the result renders after exactly two equivalent requests.
- [ ] Add a component test that returns HTTP 504 twice and asserts that the existing safe recovery message is shown after exactly two requests.
- [ ] Run `npm test -- --run src/components/analysis-workbench.test.tsx` from `web/` and record the expected RED failures before changing production code.
- [ ] Add a narrow helper that sends the screenshot request, repeats it once only when the first response status is 504, and returns the final response.
- [ ] Route `analyzeScreenshot` through that helper without changing text analysis, validation, consent, loading-state, or error-mapping behavior.
- [ ] Re-run the focused component test and confirm GREEN.
- [ ] Commit the scoped change as `fix: retry hosted OCR cold starts once`.

## Task 2: Make Professor-Facing Release Evidence Exact and Accessible

**Files:**

- Modify: `tests/test_capstone_package.py`
- Modify: `tests/test_deployment.py`
- Modify: `docs/presentation/release_snapshot.json`
- Modify: `docs/final_capstone_report.md`
- Modify: `docs/weekly_progress.md`
- Modify: `docs/presentation/demo_video_runbook.md`
- Modify: `README.md`
- Modify: `docs/professor_testing_guide.md`
- Modify: `web/src/components/professor-guide.tsx`
- Modify an existing professor-guide web test if one is present.

- [ ] Strengthen the existing capstone contract so `release_snapshot.json` must equal the live `pytest --collect-only` count instead of merely being less than or equal to it.
- [ ] Extend existing deployment/document tests to require `https://fraudlens-bharat.vercel.app` in the README, professor guide, and in-app professor guide without adding a new Python test function.
- [ ] Run `PYTHONPATH=src /opt/homebrew/bin/python3.11 -m pytest -q tests/test_capstone_package.py tests/test_deployment.py` and the relevant web test to record RED failures.
- [ ] Update the release snapshot to 358 tests with truthful capture-basis wording.
- [ ] Replace active 355-test claims with 358 in the final report, weekly progress, and demo-video runbook.
- [ ] Add the stable hosted URL as a clickable Markdown link in the README and professor testing guide and as a safe external link in the in-app guide.
- [ ] Mention the one-time screenshot retry only where it improves the professor run instructions; do not promise guaranteed uptime.
- [ ] Re-run the focused Python and web contract tests and confirm GREEN.
- [ ] Commit the scoped change as `docs: synchronize professor release evidence`.

## Task 3: Update and Visually Verify the Existing Ten-Slide Deck

**Files:**

- Modify: `docs/presentation/fraudlens-bharat-final-capstone.pptx`

- [ ] Text-extract and render the current deck to establish the RED visual/content evidence: three visible test-count callouts still report 355.
- [ ] Unpack the PPTX with the PowerPoint tooling and locate every package occurrence of the stale count.
- [ ] Use `apply_patch` on the unpacked Open XML to replace only the visible 355-test wording with 358 while preserving layout and styling.
- [ ] Clean and repack the presentation using the original deck as the package reference.
- [ ] Text-extract the repacked file and confirm that the intended 358 claims are present and no active 355-test claim remains.
- [ ] Render all ten slides, inspect the contact sheet and affected slides for clipping, overlap, font substitution, or layout movement, and complete the required fix-and-verify cycle.
- [ ] Run the capstone package tests against the updated deck.
- [ ] Commit the scoped change as `docs: refresh final capstone deck evidence`.

## Task 4: Prove the Release and Raise the Pull Request

**Files:**

- Verify all files changed by Tasks 1-3.

- [ ] Run the complete Python 3.11 suite and confirm exactly 358 collected/passing tests.
- [ ] Run the complete web unit suite, lint, type-check, and production build.
- [ ] Run the full Playwright professor flow against the built application.
- [ ] Re-run deck text extraction/render checks and the focused capstone/deployment contracts.
- [ ] Run `git diff --check`, inspect the complete diff, and verify that only intended files are staged while `.playwright-cli/` and `output/` remain untracked.
- [ ] Read and apply the verification-before-completion and finishing-a-development-branch skills.
- [ ] Push `codex/final-pitch-readiness` and create a ready pull request with an evidence-based summary, verification commands, deployment boundary, and no exaggerated claims.
