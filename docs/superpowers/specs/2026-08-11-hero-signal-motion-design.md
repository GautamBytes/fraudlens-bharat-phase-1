# Hero Signal Motion Design

## Goal

Restore the flat elliptical hero orbit shown in the approved reference and
increase its desktop diameter without changing the landing-page structure.

## Orbit Geometry

- The desktop track is a complete responsive ellipse centred at 50% horizontally
  and 38% vertically within the signal field.
- The track uses 84% of the hero width and 72% of its height.
- Marker motion uses the matching `ellipse(42% 36% at 50% 38%)` path.
- The existing tighter mobile geometry remains so the track stays within the
  viewport and avoids the calls to action.

## Motion and Appearance

- Exactly three pink-ring markers with red centres travel around the same path.
- The markers remain approximately one-third of a cycle apart.
- One continuous orbit takes 11 seconds and uses linear timing.
- The track remains faint enough to preserve headline contrast.
- All 3D perspective, depth scaling, blur, partial arcs, and diagonal transforms
  are removed.

## Accessibility and Performance

- The signal field remains decorative and `aria-hidden`.
- `prefers-reduced-motion: reduce` disables the orbit and leaves the markers at
  three separated positions.
- The effect remains CSS-only with no animation dependency or JavaScript loop.

## Verification

- Component tests require exactly one full track, exactly three markers, and no
  depth arcs.
- Stylesheet tests require the 84% × 72% geometry, matching motion path,
  11-second orbit, staggered phases, and reduced-motion handling.
- Full web tests, lint, typecheck, and the Vercel production build must pass.
- The completed change is committed and pushed to the existing feature PR.
