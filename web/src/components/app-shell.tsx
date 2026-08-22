"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useEffect, useRef, useState } from "react";

import { SiteFooter } from "./site-footer";
import { InterfaceIcon } from "./interface-primitives";

const NAVIGATION = [
  ["/", "Overview"],
  ["/relationships", "Relationships"],
  ["/research", "Research"],
  ["/guide", "Run guide"],
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
      <a className="skipLink" href="#main-content">Skip to content</a>
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
            <Link className="siteNavLink mobileAnalyzeLink" href="/analyze" onClick={() => setOpen(false)}>
              Analyze
            </Link>
            <div className="mobileBoundary">
              <strong>Educational prototype</strong>
              <span>Synthetic evidence only. Human review remains mandatory.</span>
            </div>
          </nav>
          <div className="headerTools">
            <Link className="headerCta" href="/analyze" onClick={() => setOpen(false)}>
              <span>Analyze evidence</span>
              <InterfaceIcon name="arrow" />
            </Link>
            <button
              ref={menuButton}
              className="menuButton"
              type="button"
              aria-expanded={open}
              aria-controls="primary-navigation"
              aria-label={open ? "Close menu" : "Menu"}
              onClick={() => setOpen(!open)}
            >
              <InterfaceIcon name={open ? "close" : "menu"} />
            </button>
          </div>
        </div>
      </header>
      <div className="pageSurface" id="main-content">
        {children}
      </div>
      <SiteFooter />
    </div>
  );
}
