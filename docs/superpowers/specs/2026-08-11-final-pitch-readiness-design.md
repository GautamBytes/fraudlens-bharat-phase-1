# Final Pitch-Readiness Design

## Goal

Synchronize the checked-in capstone evidence with the current 358-test release,
make the stable hosted website address explicit for professors, and make the
hosted screenshot demo recover once from the observed free-tier OCR cold-start
timeout.

## Scope

This work is one narrow pull request with three independently verifiable
changes:

1. replace stale 355-test claims with the exact current collected count in the
   release snapshot, final report, weekly progress, video runbook, and existing
   ten-slide PowerPoint;
2. publish `https://fraudlens-bharat.vercel.app` in the README, professor testing
   guide, and in-app professor guide; and
3. retry screenshot analysis exactly once when the first response is HTTP 504.

The PR must not invent new data, accuracy, supervisor feedback, deployment
capabilities, or research results.

## Evidence Synchronization

`docs/presentation/release_snapshot.json` remains the machine-readable release
snapshot and records 358 automated Python tests. The capstone package contract
must require equality between the snapshot and `pytest --collect-only`, rather
than allowing the snapshot to lag behind the current suite. Every professor-
facing 355-test statement and the visible PowerPoint callouts must become 358.

The existing deck layout, screenshots, typography, color system, slide order,
and research metrics remain unchanged. Only the stale test-count text is
updated. The edited deck must be unpacked and repacked through the PPTX tooling,
then text-extracted, rendered, and visually checked for regressions.

## Hosted Address

The stable address is `https://fraudlens-bharat.vercel.app`. It must appear as a
clickable Markdown link in the README and professor testing guide and as an
external link in the in-app run guide. Secrets, Render service URLs, and private
API credentials remain server-only and must not be added to client output.

## OCR Cold-Start Recovery

Only screenshot analysis receives automatic retry behavior. When its first
same-origin `/api/analyze-image` response has status 504, the client immediately
repeats the same request once while preserving the selected file, media type,
storage consent value, and pending state. A successful second response is
rendered normally.

There is no third attempt, no retry for text analysis, and no retry for 4xx,
500, 502, or 503 responses. If the second response fails, the existing safe,
generic error mapping is shown. The UI must not expose backend details or claim
that retry guarantees availability.

## Testing

- Use TDD for the screenshot retry: first prove one 504 followed by success does
  not currently recover, then implement the minimal two-attempt behavior.
- Cover the retry limit and preserve existing error-message tests.
- Strengthen the capstone package test to reject any future test-count drift.
- Assert the stable URL in the README, professor guide, and in-app guide.
- Run the complete Python suite, web unit suite, lint, type-check, production
  build, and Playwright professor flow.
- Validate PowerPoint content and render all ten slides for visual QA, including
  a required fix-and-verify cycle.

## Acceptance Criteria

- `pytest --collect-only` and `release_snapshot.json` both report 358.
- No active professor-facing artifact contains the stale phrase
  `355 automated tests`.
- The existing deck visibly reports 358 without layout regressions.
- The stable Vercel URL is directly available in all three guidance surfaces.
- A screenshot 504 followed by a 200 succeeds after exactly two fetches.
- A repeated 504 stops after two fetches and shows the existing recovery message.
- All verification commands pass and only intended files are committed.

## Non-Goals

This PR does not collect a real-world dataset, add a legitimate-message class,
change model artifacts or metrics, implement transformer/GNN models, claim
production accuracy, add authentication, or create the future presentation
script/video. Those research and operational boundaries remain explicit in the
current reports.
