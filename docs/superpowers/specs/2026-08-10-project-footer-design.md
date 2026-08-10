# FraudLens Bharat Project Footer Design

## Goal

Present FraudLens Bharat as one complete capstone project while moving safety guidance
out of the primary navigation area and adding clear author contact links.

## Global shell

- Remove the engine-status control from the header without changing backend health or
  readiness routes.
- Remove the amber safety strip below the header.
- Add one footer after page content on every route.
- Place the safety statement on the left side of the footer: “Educational prototype ·
  Synthetic evidence only” and “Do not enter real personal, banking or victim
  information.”
- Place a “Reach out” group on the right with LinkedIn, GitHub, and X links for Gautam
  Manchandani. External links open in a new tab and use `rel="noreferrer"`.
- Stack the footer sections at narrow widths while preserving visible keyboard focus.

## Project language

- Replace the landing-page “Phase 1 + Phase 2” label with “Explainable cyber-fraud
  triage.”
- Replace “Phase 2 · relationship intelligence” with “Relationship intelligence.”
- Do not expose phase numbering elsewhere in the professor website.

## Visual treatment

The footer stays inside the existing dark Signal Studio system: near-black canvas,
hairline top border, muted safety copy, off-white heading, and coral link hover/focus
states. It should feel like the closing edge of the product rather than a warning bar.

## Verification

- Component tests assert that the engine badge and top safety strip are absent.
- Component tests assert the footer safety text and all three exact external links.
- Page tests assert that phase wording is absent from the landing and relationship
  pages.
- Browser accessibility, mobile navigation, frontend build, and existing Python tests
  remain green.
