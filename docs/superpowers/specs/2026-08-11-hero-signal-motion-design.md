# Hero Signal Motion Design

## Goal

Give the three decorative pink hero markers quiet, continuous motion without
competing with the headline or implying live system status.

## Motion

- Each complete marker, including its pink ring and red centre, drifts 18-28px
  along the direction of its existing connector line and returns.
- The red centre adds a restrained opacity/scale pulse inside the moving ring.
- The three markers use staggered 5-8 second loops so they do not move in sync.
- Movement uses only `transform` and `opacity`, with custom easing and negative
  delays so the scene appears already in progress on load.
- Connector lines and the dotted field retain their current visual treatment.

## Accessibility and Performance

- The markers are decorative and remain `aria-hidden` with their parent field.
- `prefers-reduced-motion: reduce` freezes marker drift and centre pulses.
- No layout properties animate and no JavaScript animation loop is introduced.

## Verification

- A component contract test requires the three marker elements to remain
  present and decorative.
- A stylesheet contract test requires distinct marker drift animations, the
  centre pulse, and a reduced-motion override.
- The full web test, lint, typecheck, and production build commands must pass.
- The landing page is reviewed in a real local browser before merge.
