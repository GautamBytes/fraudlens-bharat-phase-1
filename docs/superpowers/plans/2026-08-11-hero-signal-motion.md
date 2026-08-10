# Hero Signal Motion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the three decorative hero signal markers around one visible responsive ellipse, evenly phased and easy to notice without competing with the headline.

**Architecture:** Keep `SignalField` decorative and implement the orbit entirely in CSS. A single static element draws the elliptical track. All three markers use the same motion path and keyframes, with negative delays creating one-third-cycle spacing; each marker's pseudo-element owns the independent centre pulse.

**Tech Stack:** Next.js 16, React 19, CSS motion paths and keyframes, Vitest, Testing Library

## Global Constraints

- Use one responsive elliptical path around the hero copy.
- Keep exactly three markers approximately one-third of a cycle apart.
- Complete one orbit in 11 seconds with linear movement.
- Keep the track faint and remove the obsolete straight connector lines.
- Keep the field decorative with `aria-hidden="true"`.
- Freeze orbit and pulse under `prefers-reduced-motion: reduce`.
- Do not add an animation dependency or JavaScript loop.

---

### Task 1: Shared Hero Signal Orbit

**Files:**
- Modify: `web/src/components/signal-field.tsx`
- Modify: `web/src/test/hero-signal-motion.test.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: `SignalField(): JSX.Element` and the existing `.signalNodeOne`, `.signalNodeTwo`, and `.signalNodeThree` classes.
- Produces: one `.signalOrbitTrack`, one `signal-orbit` animation shared by the three marker phases, and `signal-core-pulse` on `.signalNode::after`.

- [ ] **Step 1: Revise the motion contract test**

Require the component to render exactly three decorative signal markers, one orbit track, and no obsolete straight paths. Require the stylesheet to define `signal-orbit`, an ellipse motion path, three distinct phase delays, the centre pulse, and the existing reduced-motion override.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd web && npm test -- --run src/test/hero-signal-motion.test.tsx`

Expected: the existing marker-count assertion passes; the orbit-track and shared-orbit assertions fail because the old implementation still contains straight paths and independent drift keyframes.

- [ ] **Step 3: Implement the shared CSS orbit**

- Replace the two `.signalPath` spans with one `.signalOrbitTrack` span.
- Draw a responsive, low-contrast ellipse around the hero copy.
- Give every `.signalNode` the same elliptical `offset-path` and `signal-orbit 11s linear infinite` animation.
- Set node phase delays to `0s`, approximately `-3.667s`, and approximately `-7.333s`.
- Keep the existing marker ring treatment and `signal-core-pulse` pseudo-element.
- Remove the old `signal-drift-one`, `signal-drift-two`, and `signal-drift-three` keyframes.

- [ ] **Step 4: Run focused and complete web verification**

Run:

```bash
cd web
npm test -- --run src/test/hero-signal-motion.test.tsx
npm test -- --run
npm run lint
npm run typecheck
env VERCEL=1 npm run build
```

Expected: all focused and complete checks exit successfully.

- [ ] **Step 5: Inspect the landing page locally**

Open `http://127.0.0.1:3000`, confirm all three markers visibly travel around one ellipse without obscuring the headline, and confirm reduced motion leaves three separated static markers.

- [ ] **Step 6: Wait for visual approval before publishing**

Keep the implementation local until the user approves the browser preview. Only then commit, push, and allow the existing Vercel deployment to update.
