# Hero Signal Motion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Animate the three decorative hero signal markers with staggered path drift and a restrained inner pulse.

**Architecture:** Keep the existing `SignalField` React structure and implement motion entirely in CSS. Each marker owns its drift transform while a pseudo-element owns the independent centre pulse, avoiding transform conflicts and JavaScript animation state.

**Tech Stack:** Next.js 16, React 19, CSS keyframes, Vitest, Testing Library

## Global Constraints

- Drift each complete marker 18-28px along its existing visual direction.
- Use staggered 5-8 second loops and custom easing.
- Animate only `transform` and `opacity`.
- Keep the field decorative with `aria-hidden="true"`.
- Disable drift and pulse under `prefers-reduced-motion: reduce`.
- Do not add an animation dependency or JavaScript loop.

---

### Task 1: Animated Hero Signal Markers

**Files:**
- Create: `web/src/test/hero-signal-motion.test.tsx`
- Modify: `web/src/app/globals.css:72-86`

**Interfaces:**
- Consumes: `SignalField(): JSX.Element` and the existing `.signalNodeOne`, `.signalNodeTwo`, and `.signalNodeThree` classes.
- Produces: three CSS drift animations named `signal-drift-one`, `signal-drift-two`, and `signal-drift-three`, plus `signal-core-pulse` on `.signalNode::after`.

- [ ] **Step 1: Write the failing motion contract test**

```tsx
import { readFileSync } from "node:fs";

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SignalField } from "@/components/signal-field";

const stylesheet = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

describe("hero signal motion", () => {
  it("keeps exactly three decorative signal markers", () => {
    const { container } = render(<SignalField />);
    expect(container.querySelector(".signalField")).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelectorAll(".signalNode")).toHaveLength(3);
  });

  it("defines staggered marker drift and an inner pulse", () => {
    for (const name of ["signal-drift-one", "signal-drift-two", "signal-drift-three", "signal-core-pulse"]) {
      expect(stylesheet).toContain(`@keyframes ${name}`);
    }
    expect(stylesheet).toContain(".signalNode::after");
    expect(stylesheet).toContain("animation: none !important");
  });
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd web && npm test -- --run src/test/hero-signal-motion.test.tsx`

Expected: one test passes for the existing three decorative markers and one test fails because `signal-drift-one` is absent.

- [ ] **Step 3: Implement the CSS-only marker motion**

Replace the existing `.signalNode` and position rules with:

```css
.signalNode { position: absolute; width: 13px; height: 13px; background: rgba(255,90,79,.14); border: 1px solid rgba(255,174,168,.9); border-radius: 50%; box-shadow: 0 0 0 3px rgba(255,90,79,.08), 0 0 18px rgba(255,90,79,.24); will-change: transform; }
.signalNode::after { position: absolute; inset: 3px; background: var(--coral); border-radius: 50%; content: ""; animation: signal-core-pulse 2.8s cubic-bezier(.4,0,.2,1) infinite alternate; }
.signalNodeOne { top: 27%; left: 17%; animation: signal-drift-one 6.6s cubic-bezier(.45,.05,.55,.95) -2.1s infinite alternate; }
.signalNodeTwo { top: 16%; right: 19%; animation: signal-drift-two 7.6s cubic-bezier(.45,.05,.55,.95) -5.3s infinite alternate; }
.signalNodeThree { top: 42%; right: 28%; animation: signal-drift-three 5.8s cubic-bezier(.45,.05,.55,.95) -1.4s infinite alternate; }
```

Add these keyframes after `signal-breathe`:

```css
@keyframes signal-drift-one { from { transform: translate3d(-6px,1px,0); } to { transform: translate3d(22px,-5px,0); } }
@keyframes signal-drift-two { from { transform: translate3d(5px,-7px,0); } to { transform: translate3d(-15px,13px,0); } }
@keyframes signal-drift-three { from { transform: translate3d(-8px,5px,0); } to { transform: translate3d(14px,-8px,0); } }
@keyframes signal-core-pulse { from { opacity: .55; transform: scale(.72); } to { opacity: 1; transform: scale(1); } }
```

The existing global reduced-motion block already applies `animation: none !important` to all elements and pseudo-elements, so it freezes both layers without another override.

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

Expected: 2 focused tests pass; all web tests, lint, typecheck, and Vercel-native production build exit successfully.

- [ ] **Step 5: Inspect the landing page locally**

Run: `cd web && npm run dev`

Open `http://127.0.0.1:3000`, confirm the three markers drift asynchronously without crossing headline text, then emulate reduced motion and confirm they become static.

- [ ] **Step 6: Commit the implementation**

```bash
git add web/src/test/hero-signal-motion.test.tsx web/src/app/globals.css
git commit -m "feat: animate hero signal markers"
```
