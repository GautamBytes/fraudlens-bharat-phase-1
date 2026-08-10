"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useState } from "react";

const NAVIGATION = [
  ["/", "Evaluate", "01"],
  ["/analyze", "Analyze", "02"],
  ["/relationships", "Relationships", "03"],
  ["/research", "Research", "04"],
  ["/guide", "Run guide", "05"],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="appFrame">
      <header className="mobileHeader">
        <Link href="/" className="mobileBrand">FL<span>/</span>BHARAT</Link>
        <button
          type="button"
          aria-expanded={open}
          aria-controls="primary-navigation"
          onClick={() => setOpen(!open)}
        >
          {open ? "Close" : "Menu"}
        </button>
      </header>
      <aside className={open ? "sideRail sideRailOpen" : "sideRail"} id="primary-navigation">
        <Link href="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brandMonogram">FL</span>
          <span><strong>FraudLens</strong><small>Bharat</small></span>
        </Link>
        <p className="railCaption">Evidence-led cyber-fraud triage</p>
        <nav aria-label="Primary navigation">
          {NAVIGATION.map(([href, label, number]) => {
            const active = href === "/" ? pathname === href : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={active ? "navLink navLinkActive" : "navLink"}
                aria-current={active ? "page" : undefined}
                onClick={() => setOpen(false)}
              >
                <span>{number}</span>{label}
              </Link>
            );
          })}
        </nav>
        <div className="railBoundary">
          <strong>Educational prototype</strong>
          <span>Use synthetic evidence only. Human review is mandatory.</span>
        </div>
        <div className="railVersion">Release 1.0.0 · Phase 1 + 2</div>
      </aside>
      <div className="pageSurface">
        <div className="safetyBanner">
          <strong>Synthetic evaluation environment</strong>
          <span>Do not enter real personal, banking or victim information.</span>
        </div>
        {children}
      </div>
    </div>
  );
}
