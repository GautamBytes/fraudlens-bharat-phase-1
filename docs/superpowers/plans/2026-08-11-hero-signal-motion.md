# Enlarged Hero Orbit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the full flat elliptical hero orbit and enlarge its desktop diameter to 84% × 72%.

**Architecture:** `SignalField` renders one decorative track and three markers. CSS motion paths move all markers around the matching ellipse with negative delays; the existing global reduced-motion rule freezes them at separated points.

**Tech Stack:** Next.js 16, React 19, CSS motion paths, Vitest, Testing Library

## Global Constraints

- Render exactly one `.signalOrbitTrack` and three `.signalNode` elements.
- Use `width: 84%`, `height: 72%`, and `ellipse(42% 36% at 50% 38%)` on desktop.
- Use one 11-second linear orbit with delays `0s`, `-3.667s`, and `-7.333s`.
- Remove depth arcs, perspective, blur, and 3D transforms.
- Preserve the tighter mobile geometry and reduced-motion behavior.
- Run full verification before committing and pushing.

---

### Task 1: Restore the Enlarged Flat Orbit

**Files:**
- Modify: `web/src/test/hero-signal-motion.test.tsx`
- Modify: `web/src/components/signal-field.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: `SignalField(): JSX.Element`.
- Produces: one full orbit track and three evenly phased marker elements.

- [ ] **Step 1: Write the failing contract test**

Require one `.signalOrbitTrack`, no `.signalDepthArc`, three markers, the exact 84% × 72% track declarations, the matching ellipse motion path, `signal-orbit`, the two negative delays, and reduced-motion handling. Reject `signal-depth-orbit` and `perspective(900px)`.

- [ ] **Step 2: Verify RED**

Run: `cd web && npm test -- --run src/test/hero-signal-motion.test.tsx`

Expected: failures because the current component renders two depth arcs and the stylesheet contains 3D animation rules.

- [ ] **Step 3: Restore the component and CSS**

```tsx
<span className="signalOrbitTrack" />
<span className="signalNode signalNodeOne" />
<span className="signalNode signalNodeTwo" />
<span className="signalNode signalNodeThree" />
```

```css
.signalOrbitTrack { width: 84%; height: 72%; }
.signalNode { offset-path: ellipse(42% 36% at 50% 38%); animation: signal-orbit 11s linear infinite; }
.signalNodeOne { offset-distance: 0%; animation-delay: 0s; }
.signalNodeTwo { offset-distance: 33.333%; animation-delay: -3.667s; }
.signalNodeThree { offset-distance: 66.667%; animation-delay: -7.333s; }
@keyframes signal-orbit { from { offset-distance: 0%; } to { offset-distance: 100%; } }
```

- [ ] **Step 4: Verify GREEN and the full web package**

Run:

```bash
cd web
npm test -- --run src/test/hero-signal-motion.test.tsx
npm test -- --run
npm run lint
npm run typecheck
env VERCEL=1 npm run build
```

Expected: all commands exit successfully.

- [ ] **Step 5: Commit, push, and update the PR**

Commit only the component, stylesheet, test, design specification, and implementation plan. Push the current branch and update the existing PR description with the verified 84% orbit behavior.
