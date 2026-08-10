# FraudLens Signal Studio Redesign

## Objective

Redesign the professor website as a focused product experience that feels ready
for a capstone presentation. Keep every existing workflow and safety boundary.
Change the visual system, navigation, information hierarchy, and page composition.

The redesign takes structural cues from `swift-ai-sdk.dev`: a quiet canvas,
strong type, concise copy, product evidence as the main visual, and documentation
pages that remain easy to scan. FraudLens will not copy that site's assets,
illustrations, source code, or page compositions.

## Audience and job

A professor should understand the project boundary within 30 seconds and run a
representative analysis without reading setup documentation first. The website
must also support a deeper review of relationship evidence, research results,
limitations, and local execution.

## Product identity

The visual concept is **FraudLens Signal Studio**. It treats the website as a
calm evidence-analysis product rather than an administrative dashboard.

The signature element is a masked signal field: a halftone network derived from
the visual language of redacted identifiers and connected incidents. It appears
behind the landing-page hero and nowhere else at full strength. This gives the
project a recognizable motif without turning every screen into a cyber-security
illustration.

### Design tokens

- Signal black: `#171717`
- Cloud: `#F7F7F5`
- Paper: `#FFFFFF`
- Signal coral: `#FF5A4F`
- Review amber: `#F3A712`
- Evidence teal: `#087F78`
- Muted ink: `#666A70`
- Hairline: `#E2E2DE`

Instrument Sans will carry display and body copy. IBM Plex Mono will label model
outputs, evidence fields, and technical metadata. Removing Sora from display
headlines will reduce the blocky dashboard character of the current site.

Coral marks suspicious or high-risk signals. Amber marks review and uncertainty.
Teal marks verified evidence and ready states. Every status also includes text or
an icon so color never carries the meaning alone.

## Global shell

Replace the fixed dark sidebar with a slim horizontal header. The header contains
the FraudLens wordmark, Evaluate, Analyze, Relationships, Research, Run guide,
backend status, and a compact mobile menu. The active route uses a coral underline.

A narrow safety notice sits below the header. It remains visible without consuming
the left quarter of every page. On mobile, the navigation opens as an accessible
sheet and returns focus to its trigger when closed.

Use a maximum content width of 1180 pixels. Landing-page sections receive large
vertical intervals. Workflow pages use tighter spacing so controls and results
fit within a professor's laptop viewport.

## Landing page

The hero uses a centered composition:

```text
              FraudLens Bharat · Phase 1 + Phase 2
       Review suspicious messages with evidence in context.
         Short boundary statement and two clear actions

       [ live analysis trace based on a synthetic example ]
```

The masked signal field sits behind the upper hero. The trace module is the hero's
product example: synthetic text enters on the left, masked entities and signals
appear through the middle, and a reviewable decision appears on the right. It links
to the real analyzer rather than duplicating analysis state on the landing page.

Below the hero:

1. A compact capability mosaic explains text/OCR, explainability, privacy, and
   relationship intelligence using actual outputs instead of generic feature icons.
2. A research boundary section separates the experimental candidate from the
   deployed runtime and keeps the small-dataset limitation adjacent to both metrics.
3. A final call to action directs professors to the six-to-eight-minute evaluation
   path and the local run guide.

## Analyze page

Use a centered workflow with a two-column desktop composition after a result exists.
The left column holds the message/screenshot input. The right column reveals the
decision, uncertainty, risk, evidence, and complaint draft. Before analysis, the
input occupies the readable center of the page and prepared examples remain visible.

The result hierarchy is:

1. category, decision state, confidence, and risk;
2. extracted masked entities and detected signals;
3. explanation and OCR provenance;
4. reviewable complaint draft and human-control boundary.

Use rounded 14-pixel surfaces, hairline borders, and low shadows. Avoid nested cards
when a divider or typographic group can establish hierarchy. Storage remains off and
its wording continues to specify synthetic evidence.

## Relationships page

Present the relationship graph as a signal map with a light dotted field, restrained
node colors, and a compact control bar. Explain the synthetic seed action before the
empty graph. Once data exists, place cluster metrics above the graph and the truthful
edge table below it.

The visual graph must follow the API edge data. It must not imply links that the
adjacent table does not contain. Reset stays explicit and visually separated from
the primary seed and refresh actions.

## Research page

Adopt a documentation-style frame on wide screens: a small section index on the left,
the research narrative and tables in the center, and an on-page outline on the right.
Collapse both auxiliary columns on smaller screens.

Lead with the candidate-versus-runtime comparison, then show all approaches, metric
rationale, robustness evidence, dataset boundaries, and limitations. Keep source
citations close to external claims. Tables use captions, sticky headers when useful,
and horizontal scrolling on narrow screens.

## Run guide

Use the same documentation frame as Research. Organize the guide around a professor's
sequence: hosted evaluation, complete local run, development run, verification,
reset, and troubleshooting. Commands remain copyable and use the mono face. Service
health and expected responses stay visible beside the relevant commands.

## Motion and interaction

- Reveal the hero trace in one short sequence after first paint.
- Animate the signal field with a slow opacity drift, not continuous travel.
- Use 150-220 ms transitions for navigation, tabs, buttons, and result disclosure.
- Stop nonessential motion under `prefers-reduced-motion`.
- Keep focus rings visible and never animate layout during keyboard navigation.

## Error, loading, and empty states

The header service badge reports ready, waking, or unavailable. It retries cold starts
on a bounded timer and offers an explicit retry control.

Input errors appear beside the affected control. API failures preserve entered text
or the selected screenshot. Empty graph and research states tell the professor which
action supplies evidence. No error surface exposes backend exception text, secrets,
or internal URLs.

## Responsive behavior

- Desktop: horizontal navigation, wide hero, documentation sidebars, two-column
  analysis results.
- Tablet: compact navigation, single documentation index, stacked analysis result.
- Mobile: menu sheet, single-column sections, scrollable tables, full-width actions,
  and no loss of evidence fields.

The target widths are 1440, 1024, 768, and 390 pixels. The website must remain usable
at 200% browser zoom.

## Architecture and component boundaries

The redesign changes presentation code only. Existing Next.js route handlers,
FastAPI contracts, request limits, demo authentication, and Python behavior remain
authoritative.

Refactor the web layer into these focused units:

- `AppShell`: top navigation, safety notice, mobile menu, and service badge.
- `SignalField`: decorative, hidden from assistive technology, reduced-motion aware.
- `AnalysisTrace`: typed landing-page illustration using committed synthetic data.
- `PageIntro`: shared route title, eyebrow, description, and optional actions.
- `DocsFrame`: shared Research and Run guide index/content/outline layout.
- Existing workbench and evidence components: preserve data fetching and state while
  receiving the new visual composition.

CSS tokens remain global. Page-specific layouts use narrowly named classes so the
redesign does not recreate a single monolithic stylesheet with conflicting selectors.

## Testing and acceptance

The redesign is complete when:

- existing Python and web behavior tests pass;
- component tests cover the new navigation, mobile menu, signal trace, and docs frame;
- Playwright completes text analysis, screenshot validation, graph seed/reset, route
  navigation, keyboard focus, and automated accessibility checks;
- all five routes render without horizontal page overflow at the target widths;
- reduced motion disables the signal animation and staged reveal;
- before-and-after screenshots exist for Evaluate, Analyze, Relationships, Research,
  and Run guide;
- page copy retains the synthetic-data, small-dataset, abstention, privacy, and
  human-review boundaries.

## Out of scope

- Changes to model training, evaluation metrics, OCR, database, or API contracts.
- New user accounts, professor authentication, or persistent cloud storage.
- Copying code, assets, logos, or illustrations from the reference website.
- Removing the existing Docker and local-development paths.
