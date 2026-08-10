# Hero Signal Motion Design

## Goal

Make the three decorative pink hero markers visibly orbit the landing-page
headline on one shared ellipse without obscuring content or implying live
system status.

## Motion

- All three complete markers share one responsive elliptical motion path around
  the hero copy and remain approximately one-third of a cycle apart.
- One orbit takes 11 seconds. Negative delays make the markers appear already
  in motion when the page loads.
- The pink outer ring travels with a restrained red-centre opacity/scale pulse.
- A faint static elliptical track makes the movement readable against the
  existing dotted field without crossing or reducing headline contrast.
- The two obsolete straight connector lines are removed from the field.

## Accessibility and Performance

- The markers are decorative and remain `aria-hidden` with their parent field.
- `prefers-reduced-motion: reduce` freezes the three markers at separated points
  on the visible ellipse and disables centre pulses.
- CSS motion-path distance, `transform`, and `opacity` are the only animated
  values; no layout property or JavaScript animation loop is introduced.

## Verification

- A component contract test requires the three marker elements to remain
  present and decorative.
- A stylesheet contract test requires the shared ellipse, one orbit animation,
  three staggered phases, the centre pulse, and a reduced-motion override.
- The full web test, lint, typecheck, and production build commands must pass.
- The landing page is reviewed in a real local browser before merge.
