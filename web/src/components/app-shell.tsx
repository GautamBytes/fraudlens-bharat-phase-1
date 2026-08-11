"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useEffect, useRef, useState } from "react";

import { SiteFooter } from "./site-footer";

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
  const menuButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      setOpen(false);
      menuButton.current?.focus();
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [open]);

  return (
    <div className="appFrame">
      <header className="siteHeader">
        <div className="siteHeaderInner">
          <Link href="/" className="siteBrand" onClick={() => setOpen(false)}>
            <span className="siteBrandMark" aria-hidden="true">FL</span>
            <span className="siteBrandName">FraudLens <small>Bharat</small></span>
          </Link>
          <nav
            aria-label="Primary navigation"
            className={open ? "siteNav siteNavOpen" : "siteNav"}
            id="primary-navigation"
          >
            {NAVIGATION.map(([href, label]) => {
              const active = href === "/" ? pathname === href : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={active ? "siteNavLink siteNavLinkActive" : "siteNavLink"}
                  aria-current={active ? "page" : undefined}
                  onClick={() => setOpen(false)}
                >
                  {label}
                </Link>
              );
            })}
            <div className="mobileBoundary">
              <strong>Educational prototype</strong>
              <span>Synthetic evidence only. Human review remains mandatory.</span>
            </div>
          </nav>
          <div className="headerTools">
            <button
              ref={menuButton}
              className="menuButton"
              type="button"
              aria-expanded={open}
              aria-controls="primary-navigation"
              aria-label={open ? "Close menu" : "Menu"}
              onClick={() => setOpen(!open)}
            >
              <span aria-hidden="true">{open ? "×" : "☰"}</span>
            </button>
          </div>
        </div>
      </header>
      <div className="pageSurface">
        {children}
      </div>
      <SiteFooter />
    </div>
  );
}
