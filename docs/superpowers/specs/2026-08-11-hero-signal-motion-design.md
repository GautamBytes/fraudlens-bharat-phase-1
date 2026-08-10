# Hero Signal Motion Design

## Goal

Replace the flat hero ellipse with a convincing diagonal 3D signal orbit. The
three decorative markers should appear to move into and out of the page while
the headline remains readable and visually dominant.

## Spatial Direction

- The orbital plane runs diagonally through the scene.
- Its top-left region is the far side of the orbit.
- Its bottom-right region is the near side, appearing to emerge toward the
  viewer.
- The three markers remain approximately one-third of a cycle apart.

## Depth Treatment

- Perspective and 3D transforms provide the primary spatial movement.
- A marker approaching the bottom-right near side becomes larger, sharper,
  brighter, and more strongly illuminated.
- A marker moving toward the top-left far side becomes smaller, dimmer, and
  slightly blurred.
- The current continuous flat ellipse is removed. Two restrained partial arcs
  indicate the trajectory without enclosing the headline in a large outline.
- Far-side markers visually recede behind the hero copy; near-side markers
  appear closer to the viewer without blocking actionable content.

## Motion

- All three markers share one continuous 11-second linear orbit.
- Negative delays distribute them evenly and make the scene appear active on
  first paint.
- The pink ring and red centre remain visually intact at every depth.
- The red centre may vary subtly with the parent marker's depth but does not
  use a separate attention-seeking pulse.

## Accessibility and Performance

- The complete signal field remains decorative and `aria-hidden`.
- `prefers-reduced-motion: reduce` disables the orbit and leaves three markers
  at separated diagonal depth positions.
- The effect uses CSS transforms, opacity, and a restrained filter only. It
  introduces no JavaScript animation loop or animation dependency.
- Only the three markers receive targeted compositor hints.

## Responsive Behavior

- Desktop and tablet retain the full diagonal depth sweep around the headline.
- Mobile uses a tighter path so markers stay inside the viewport and do not
  cover navigation, copy, or calls to action.
- The same top-left-far and bottom-right-near reading is preserved at every
  supported width.

## Verification

- Component tests require exactly three decorative markers and partial depth
  arcs, with no continuous ellipse track.
- Stylesheet tests require perspective, 3D preservation, shared orbit timing,
  three staggered phases, near/far depth states, and reduced-motion handling.
- Full web tests, lint, typecheck, and the Vercel production build must pass.
- Desktop and mobile previews are visually reviewed in a real browser before
  any implementation commit or push.
