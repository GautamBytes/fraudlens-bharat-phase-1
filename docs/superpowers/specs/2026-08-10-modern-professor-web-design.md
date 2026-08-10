# FraudLens Bharat Modern Professor Web Design

## Objective

Replace the Streamlit-first professor experience with a polished web application
that is simple to open, visually credible in a capstone review, and capable of
exercising the real FraudLens text, OCR, complaint-draft, privacy, and graph
workflows. Vercel serves the web application; the existing containerized Python
runtime remains the authoritative analysis engine on Render. Docker Compose
remains the complete offline fallback.

## Audience and primary job

The primary audience is a professor evaluating a student capstone. The web
application's single job is to let that reviewer understand the system and run
the important workflows without installing development tools or learning the
repository structure.

## Architecture

The browser communicates only with same-origin Next.js route handlers. Those
handlers validate bounded requests and proxy them to the FastAPI service using
a server-only demo key. The Render URL and key never appear in browser code.

```text
Professor browser
    -> Next.js UI on Vercel
    -> same-origin route handlers
    -> authenticated FastAPI container on Render
    -> model, OCR, SQLite demo state
```

The hosted transport accepts screenshots up to 4,000,000 bytes so it stays
below Vercel's 4.5 MB function payload boundary. The Python API retains its
existing 5 MiB boundary for Docker and direct local use.

## Visual direction

The interface uses an "evidence workbench" rather than a generic cyber-neon
dashboard. A dark ink navigation rail frames a light, document-like analysis
surface. Saffron identifies active investigation steps, coral identifies risk,
and teal identifies verified evidence. Fine grid lines and clipped case-file
corners reference evidence handling without imitating law-enforcement software.

### Design tokens

- Ink: `#101827`
- Paper: `#F7F8FA`
- Surface: `#FFFFFF`
- Saffron: `#F6A800`
- Signal coral: `#E9505A`
- Evidence teal: `#087F78`
- Slate: `#526071`

The display face is Sora, body text uses Instrument Sans, and compact evidence
labels use IBM Plex Mono. Fonts are delivered through the Next.js font system.
Risk colors are never the only way information is communicated.

The signature interaction is an evidence rail that visibly transforms an input
into extracted signals, an uncertainty-aware decision, and a complaint draft.
Motion is limited to one staged result reveal and small state transitions, and
is removed when the user prefers reduced motion.

## Information architecture

### Evaluate

The landing page explains the project boundary and provides a guided four-step
evaluation path. It reports backend readiness and handles a sleeping Render
service with a specific waking message and automatic retry.

### Analyze

Text and screenshot inputs share one result model. Prepared synthetic examples
are prominent. Results show category, confidence, abstention, risk score,
evidence, URL signals, explanation, OCR metadata, and complaint draft. Copying
the complaint draft is explicit. Storage starts off.

### Relationships

The professor can seed two synthetic incidents that share a masked host, change
the repeated-case threshold, refresh the graph, inspect bounded cluster metrics,
and reset all demo data. The page states that this is observational relationship
evidence, not graph-based fraud detection.

### Research

The page separates the 75.0% research character-TF-IDF candidate from the 50.0%
deployed calibrated runtime. It shows Macro-F1, coverage, model size, dataset
scope, and limitations without presenting external studies as a leaderboard.

### Run guide

The in-app guide and `docs/professor_testing_guide.md` explain:

- how to use the hosted evaluation URL;
- the recommended professor test sequence and expected boundaries;
- how to run the complete stack with Docker Compose;
- how to run the Python API and Next.js frontend separately for development;
- required environment variables and secret handling;
- cold-start, ephemeral-storage, and failure-safe behavior;
- how to verify health, readiness, tests, and reset behavior.

## Hosted demo safeguards

- A persistent banner says the hosted service is an educational prototype and
  must not receive real personal or financial information.
- Case storage defaults to false and requires an explicit synthetic-demo action.
- Screenshot bytes are never retained.
- The Render filesystem is treated as ephemeral.
- A reset action clears hosted demo cases.
- Data endpoints require a constant-time checked server secret when hosted demo
  authentication is configured.
- Health remains non-sensitive; API responses remain `no-store`.
- The web proxy uses explicit timeouts, request limits, and generic errors.

## Error and empty states

- A cold backend produces a waking state with elapsed guidance, not a generic
  network error.
- OCR format, size, no-text, timeout, and unavailable states provide distinct
  recovery instructions without exposing backend details.
- Empty graph state directs the professor to seed synthetic incidents.
- Every retry is explicit and never repeats a state-changing request silently.

## Accessibility and responsive behavior

- All flows are usable by keyboard.
- Focus indicators meet contrast requirements.
- Semantic headings, status regions, form labels, and table captions are used.
- Mobile collapses navigation into a sheet and stacks the evidence rail without
  hiding any result.
- Reduced motion is respected.
- Automated accessibility checks run against the major routes.

## Testing

- Python tests cover optional hosted-demo authentication without changing local
  defaults.
- TypeScript unit tests cover schemas, API error mapping, upload limits, and
  research claims.
- Component tests cover guided demo states, results, empty graph, and errors.
- Playwright covers text analysis, screenshot validation, graph seeding/reset,
  responsive navigation, keyboard focus, and the professor run guide.
- CI builds the Next.js application and runs lint, typecheck, unit, and browser
  tests in addition to the existing Python and container checks.

## Delivery sequence

1. Modern web client plus the minimal authenticated backend boundary.
2. Vercel/Render deployment configuration, professor run guide, and deployment
   smoke verification.

The Streamlit implementation remains available during parity work and is not
removed until the modern web application passes all required workflows.
