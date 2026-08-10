import type { ReactNode } from "react";

export type DocsLink = { href: string; label: string };

export function DocsFrame({ index, outline, children }: { index: DocsLink[]; outline: DocsLink[]; children: ReactNode }) {
  return (
    <div className="docsFrame">
      <nav className="docsIndex" aria-label="Section index">
        <span className="docsNavLabel">Sections</span>
        {index.map((link) => <a key={link.href} href={link.href}>{link.label}</a>)}
      </nav>
      <article className="docsContent">{children}</article>
      <aside className="docsOutline" aria-label="On this page">
        <span className="docsNavLabel">On this page</span>
        {outline.map((link) => <a key={link.href} href={link.href}>{link.label}</a>)}
      </aside>
    </div>
  );
}
