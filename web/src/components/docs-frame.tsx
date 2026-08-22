"use client";

import type { ReactNode } from "react";
import { useState } from "react";

export type DocsLink = { href: string; label: string };

export function DocsFrame({ index, outline, children }: { index: DocsLink[]; outline: DocsLink[]; children: ReactNode }) {
  const [activeHref, setActiveHref] = useState(index[0]?.href ?? "");
  const renderLink = (link: DocsLink) => (
    <a key={link.href} href={link.href} aria-current={activeHref === link.href ? "location" : undefined} onClick={() => setActiveHref(link.href)}>
      {link.label}
    </a>
  );
  return (
    <div className="docsFrame">
      <nav className="docsIndex" aria-label="Section index">
        <span className="docsNavLabel">Sections</span>
        {index.map(renderLink)}
      </nav>
      <article className="docsContent">{children}</article>
      <aside className="docsOutline" aria-label="On this page">
        <span className="docsNavLabel">On this page</span>
        {outline.map(renderLink)}
      </aside>
    </div>
  );
}
