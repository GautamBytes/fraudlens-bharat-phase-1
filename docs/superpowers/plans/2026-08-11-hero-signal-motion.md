# Diagonal 3D Hero Signal Orbit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat hero ellipse with three evenly phased markers that travel through a top-left-far to bottom-right-near 3D orbit.

**Architecture:** Keep the animation CSS-only and decorative. Three marker elements share one transform keyframe sequence with negative delays; `translate3d`, perspective, scale, opacity, blur, and z-index communicate depth, while two static partial arcs replace the continuous ellipse.

**Tech Stack:** Next.js 16, React 19, CSS 3D transforms and keyframes, Vitest, Testing Library

## Global Constraints

- Keep exactly three markers approximately one-third of a cycle apart.
- Use an 11-second continuous linear orbit.
- Treat top-left as far and bottom-right as near.
- Remove the continuous ellipse and render exactly two restrained partial arcs.
- Preserve each marker's pink ring and red centre without a separate pulse.
- Keep the field `aria-hidden="true"` and freeze it under reduced motion.
- Add no JavaScript animation loop or animation dependency.
- Do not commit or push the implementation before visual approval.

---

### Task 1: Diagonal 3D Signal Orbit

**Files:**
- Modify: `web/src/components/signal-field.tsx`
- Modify: `web/src/app/globals.css`
- Modify: `web/src/test/hero-signal-motion.test.tsx`

**Interfaces:**
- Consumes: `SignalField(): JSX.Element`.
- Produces: two `.signalDepthArc` elements, three `.signalNode` elements, and one shared `signal-depth-orbit` CSS animation.

- [ ] **Step 1: Write the failing motion contract**

```tsx
it("renders three markers and two partial depth arcs", () => {
  const { container } = render(<SignalField />);
  expect(container.querySelector(".signalField")).toHaveAttribute("aria-hidden", "true");
  expect(container.querySelectorAll(".signalNode")).toHaveLength(3);
  expect(container.querySelectorAll(".signalDepthArc")).toHaveLength(2);
  expect(container.querySelectorAll(".signalOrbitTrack")).toHaveLength(0);
});

it("defines one staggered diagonal 3D orbit", () => {
  expect(stylesheet.includes("@keyframes signal-depth-orbit")).toBe(true);
  expect(stylesheet.includes("perspective(900px)")).toBe(true);
  expect(stylesheet.includes("transform-style: preserve-3d")).toBe(true);
  expect(stylesheet.includes("translate3d(")).toBe(true);
  expect(stylesheet.includes("filter: blur(")).toBe(true);
  expect(stylesheet.includes("animation-delay: -3.667s")).toBe(true);
  expect(stylesheet.includes("animation-delay: -7.333s")).toBe(true);
  expect(stylesheet.includes("animation: none !important")).toBe(true);
  expect(stylesheet.includes("signal-core-pulse")).toBe(false);
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd web && npm test -- --run src/test/hero-signal-motion.test.tsx`

Expected: both tests fail because the component still renders `.signalOrbitTrack` and the stylesheet still defines the flat `signal-orbit` motion path.

- [ ] **Step 3: Replace the flat track with depth arcs**

```tsx
<span className="signalDepthArc signalDepthArcBack" />
<span className="signalDepthArc signalDepthArcFront" />
<span className="signalNode signalNodeOne" />
<span className="signalNode signalNodeTwo" />
<span className="signalNode signalNodeThree" />
```

The back arc shows only a faint top-left trajectory segment. The front arc shows only a brighter bottom-right segment. Neither arc animates.

- [ ] **Step 4: Implement the shared depth animation**

Define responsive orbit coordinates as custom properties on `.signalField`. Place every marker at the same orbit centre, then animate eight transform states around the loop. The near state uses positive Z, larger scale, full opacity, no blur, and z-index 4. The far state uses negative Z, smaller scale, reduced opacity, restrained blur, and z-index 1. Use these phase rules:

```css
.signalNodeOne { animation-delay: 0s; }
.signalNodeTwo { animation-delay: -3.667s; }
.signalNodeThree { animation-delay: -7.333s; }
```

Provide non-animated near, side, and far transforms on those three classes so the global reduced-motion rule leaves a legible diagonal composition.

- [ ] **Step 5: Run focused and complete verification**

Run:

```bash
cd web
npm test -- --run src/test/hero-signal-motion.test.tsx
npm test -- --run
npm run lint
npm run typecheck
env VERCEL=1 npm run build
```

Expected: all tests and static checks pass; the production build completes successfully.

- [ ] **Step 6: Visually inspect desktop and mobile**

Open `http://127.0.0.1:3000`. Confirm the markers become larger and sharper toward bottom-right, smaller and dimmer toward top-left, never cover the calls to action, and remain inside a 390×844 viewport.

- [ ] **Step 7: Hold for approval**

Leave the implementation uncommitted and unpushed until the user approves the local browser preview.
