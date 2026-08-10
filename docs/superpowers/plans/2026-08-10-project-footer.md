# Project Footer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the prototype warning into a global contact footer, remove the engine badge, and present FraudLens Bharat as one project without phase labels.

**Architecture:** Add a focused `SiteFooter` component and let `AppShell` own its placement after route content. Remove the unused visual status component and its stale recovery copy while keeping health APIs intact. Update only user-facing phase labels and cover the new global contract with component and browser tests.

**Tech Stack:** Next.js 16, React 19, TypeScript, Vitest, Testing Library, Playwright, CSS.

## Global Constraints

- Keep the existing dark Signal Studio design system.
- Preserve all FastAPI health, readiness, analysis, OCR, graph, and storage behavior.
- Use the exact LinkedIn, GitHub, and X URLs from the approved specification.
- External contact links open in a new tab with `rel="noreferrer"`.
- Do not expose phase numbering in professor-website copy.

---

### Task 1: Global footer and simplified header

**Files:**
- Create: `web/src/components/site-footer.tsx`
- Create: `web/src/components/site-footer.test.tsx`
- Modify: `web/src/components/app-shell.tsx`
- Modify: `web/src/components/app-shell.test.tsx`
- Delete: `web/src/components/service-status.tsx`
- Delete: `web/src/components/service-status.test.tsx`
- Modify: `web/src/components/professor-guide.tsx`
- Modify: `web/src/components/professor-guide.test.tsx`
- Modify: `web/src/components/analysis-workbench.tsx`
- Modify: `web/src/components/analysis-workbench.test.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Produces: `SiteFooter(): JSX.Element`, rendered once by `AppShell` after `children`.
- Removes: `ServiceStatus`, the top `.safetyNotice`, and status-dependent recovery copy; backend health routes remain unchanged.

- [ ] **Step 1: Write failing footer and shell tests**

```tsx
render(<SiteFooter />);
expect(screen.getByRole("contentinfo")).toHaveTextContent("Educational prototype");
expect(screen.getByRole("link", { name: "LinkedIn" })).toHaveAttribute("href", "https://www.linkedin.com/in/gautam-manchandani/");
expect(screen.getByRole("link", { name: "GitHub" })).toHaveAttribute("href", "https://github.com/GautamBytes");
expect(screen.getByRole("link", { name: "X" })).toHaveAttribute("href", "https://x.com/GautamM96");

render(<AppShell><p>Professor workspace</p></AppShell>);
expect(screen.queryByText(/engine ready|checking engine/i)).not.toBeInTheDocument();
expect(screen.queryByRole("region", { name: "Safety notice" })).not.toBeInTheDocument();
expect(screen.getByRole("contentinfo")).toBeVisible();
```

- [ ] **Step 2: Run tests and verify RED**

Run: `cd web && npm test -- --run src/components/site-footer.test.tsx src/components/app-shell.test.tsx`

Expected: FAIL because `SiteFooter` does not exist and `AppShell` still renders the status and top notice.

- [ ] **Step 3: Implement the footer and shell integration**

```tsx
const CONTACTS = [
  ["LinkedIn", "https://www.linkedin.com/in/gautam-manchandani/"],
  ["GitHub", "https://github.com/GautamBytes"],
  ["X", "https://x.com/GautamM96"],
] as const;

export function SiteFooter() {
  return (
    <footer className="siteFooter">
      <div className="siteFooterInner">
        <div className="footerSafety">
          <strong>Educational prototype · Synthetic evidence only</strong>
          <span>Do not enter real personal, banking or victim information.</span>
        </div>
        <nav aria-label="Reach out" className="footerContacts">
          <span>Reach out</span>
          {CONTACTS.map(([label, href]) => <a key={label} href={href} target="_blank" rel="noreferrer">{label}</a>)}
        </nav>
      </div>
    </footer>
  );
}
```

Remove the `ServiceStatus` component, import/render, styles, and `.safetyNotice` block from `AppShell`, then render `<SiteFooter />` after `children`. Update the Run Guide and generic analysis error to use actionable retry guidance without referring to a removed status control. Add dark footer layout, hover, focus, and stacked mobile rules in `globals.css`.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `cd web && npm test -- --run src/components/site-footer.test.tsx src/components/app-shell.test.tsx`

Expected: both test files pass.

### Task 2: Single-project language

**Files:**
- Create: `web/src/components/project-language.test.tsx`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/relationships/page.tsx`
- Modify: `web/e2e/professor-flow.spec.ts`

**Interfaces:**
- Produces: landing kicker `Explainable cyber-fraud triage` and relationship eyebrow `Relationship intelligence`.

- [ ] **Step 1: Write a failing website-copy test**

```tsx
render(<EvaluatePage />);
expect(screen.getByText("Explainable cyber-fraud triage")).toBeVisible();
expect(screen.queryByText(/phase 1|phase 2/i)).not.toBeInTheDocument();

render(<RelationshipsPage />);
expect(screen.getByText("Relationship intelligence")).toBeVisible();
expect(screen.queryByText(/phase 1|phase 2/i)).not.toBeInTheDocument();
```

Add an E2E assertion that the footer is present on the landing page and that no phase label appears.

- [ ] **Step 2: Run tests and verify RED**

Run: `cd web && npm test -- --run src/components/project-language.test.tsx`

Expected: FAIL because both old phase labels remain.

- [ ] **Step 3: Replace only the phase labels**

In `page.tsx`, render `<p className="heroKicker">Explainable cyber-fraud triage</p>`. In `relationships/page.tsx`, set `eyebrow="Relationship intelligence"`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `cd web && npm test -- --run src/components/project-language.test.tsx`

Expected: PASS.

### Task 3: Full verification and delivery

**Files:**
- Verify all modified website files.

- [ ] **Step 1: Run complete frontend verification**

```bash
cd web
npm test -- --run
npm run lint
npm run typecheck
npm run build
npx playwright test
```

Expected: all unit tests, lint, TypeScript, production build, responsive checks, and accessibility journeys pass.

- [ ] **Step 2: Verify repository copy and formatting**

Run: `rg -n "Phase 1|Phase 2|Engine ready|Checking engine" web/src web/e2e && git diff --check`

Expected: no user-facing phase/status matches except isolated service-status component tests, and no whitespace errors.

- [ ] **Step 3: Commit and push**

```bash
git add web/src/components/site-footer.tsx web/src/components/site-footer.test.tsx web/src/components/app-shell.tsx web/src/components/app-shell.test.tsx web/src/components/project-language.test.tsx web/src/app/page.tsx web/src/app/relationships/page.tsx web/src/app/globals.css web/e2e/professor-flow.spec.ts docs/superpowers/plans/2026-08-10-project-footer.md
git commit -m "feat: add project contact footer"
git push
```
