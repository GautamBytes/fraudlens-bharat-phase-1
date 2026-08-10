# Recorded Evidence Tour and Workspace Refinement

## Goal

Help professors understand FraudLens Bharat before interacting with it, while bringing
Analyze, Relationships, Research, and Run Guide to the same visual and interaction
quality as the landing page.

## Design direction

The website remains a dark Signal Studio interface with off-white typography, charcoal
surfaces, coral actions, teal evidence labels, restrained amber warnings, and visible
hairline structure. Inner pages should feel like parts of one investigation product,
not separate documentation screens.

## Landing-page recorded walkthrough

Add a section after the capability mosaic and before the research boundary. Its heading
is “See the system before you run it.” It contains three numbered evidence stories:

1. **Classify a suspicious message** — a completed text-analysis workspace showing the
   synthetic input, masked signals, calibrated decision, confidence, and complaint draft.
2. **Extract evidence from a screenshot** — a completed screenshot-analysis workspace
   showing OCR source metadata, extracted text, and the same review output model.
3. **Connect repeated masked signals** — a seeded relationship workspace showing two
   synthetic cases linked through one masked entity, with the graph and evidence ledger.

Each story pairs a browser-framed screenshot with concise copy that states the synthetic
input, the observable output, what to inspect, and a direct link to the relevant route.
Desktop alternates image and copy placement; mobile stacks copy above the image. The
section is a linear narrative rather than tabs so no evidence is hidden.

### Screenshot provenance

- Generate screenshots from the current Next.js UI at 1440px using deterministic,
  synthetic fixtures already exercised by browser tests.
- Store optimized PNG files under `web/public/showcase/` with stable names:
  `text-analysis.png`, `screenshot-analysis.png`, and `relationship-graph.png`.
- Add a small “Recorded synthetic demonstration” label to every story.
- Never claim that a replayed screenshot is a live request or a production benchmark.
- Do not include real personal information, bank data, victim data, or unmasked entities.
- Add a repeatable Playwright capture script so screenshots can be regenerated after UI
  changes instead of edited manually.

## Analyze workspace

Keep both text and screenshot paths in one workspace. Improve the ready state with a
compact “What happens next” rail and a synthetic-example cue rather than a large empty
surface. In the completed state, retain the two-column intake/result layout but strengthen
the hierarchy: decision and confidence first, evidence signals second, complaint draft
last. Keep storage disabled by default and visible beside the intake heading. Existing
limits, API calls, OCR handling, and error messages do not change.

## Relationships workspace

Treat the page as an investigation canvas. Keep threshold, build, refresh, and clear
controls together in a compact toolbar. Add a short three-step cue for building the
synthetic example. When data exists, show summary metrics before the graph, the graph as
the dominant surface, and the complete edge table directly below it. Empty state copy
must explain that the professor can build a safe two-case example. Masking and graph
semantics do not change.

## Research workspace

Keep the documentation frame and honest evidence boundary. Improve scanability with a
compact headline metric strip, stronger candidate-versus-runtime cards, and restrained
horizontal bars for accuracy, Macro-F1, and coverage. The table remains the source of
exact values. Experimental and deployed claims must remain visually and verbally
separate; no metric, row count, dataset limitation, or model name may be altered.

## Run Guide workspace

Open with three evaluation paths: hosted walkthrough, complete Docker run, and split
development run. Use numbered step cards for the hosted path, code panels with copy-friendly
layout for local commands, and a final recovery checklist. Keep every command, environment
boundary, storage warning, and synthetic-only instruction accurate. The page remains
usable without JavaScript-only copy controls.

## Component boundaries

- `RecordedDemoTour` owns the landing-page stories and image metadata.
- `RecordedDemoStory` renders one responsive image/copy pair.
- Existing `AnalysisWorkbench`, `RelationshipWorkbench`, `ResearchEvidence`, and
  `ProfessorGuide` retain their data and request responsibilities; refinements stay within
  their presentation structure and shared CSS.
- A Playwright capture file owns deterministic screenshot generation and does not run in
  the default professor journey suite.

## Accessibility and responsive behavior

- Screenshots use descriptive alt text that conveys the result, not every visible word.
- Recorded screenshots are supplementary; all conclusions also appear as text.
- Preserve visible keyboard focus, reduced-motion behavior, semantic headings, table
  captions, and labelled regions.
- At 768px and below, page introductions, toolbars, result panels, and walkthrough stories
  stack without horizontal page overflow.
- Screenshot frames may scroll internally only when required; the page itself must not
  gain horizontal overflow.

## Verification

- Component tests cover all three walkthrough stories, exact image paths, synthetic labels,
  descriptive alt text, and direct route links.
- Existing workbench tests continue to cover storage, analysis, screenshot limits, graph
  seeding, reset, and error behavior.
- New structural tests cover the refined ready/completed hierarchy and research metric bars.
- Playwright continues to cover the professor flow, seeded graph, mobile/tablet navigation,
  reduced motion, and axe accessibility on every route.
- A capture command regenerates all three showcase images and a repository test verifies
  that each committed image exists and is non-empty.
