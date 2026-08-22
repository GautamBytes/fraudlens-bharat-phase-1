const CONTACTS = [
  ["LinkedIn", "https://www.linkedin.com/in/gautam-manchandani/"],
  ["GitHub", "https://github.com/GautamBytes"],
  ["X", "https://x.com/GautamM96"],
] as const;

export function SiteFooter() {
  return (
    <footer className="siteFooter">
      <div className="siteFooterInner">
        <div className="footerIdentity">
          <div className="footerBrand"><span className="siteBrandMark" aria-hidden="true">FL</span><strong>FraudLens Bharat</strong></div>
          <p>Explainable cyber-fraud evidence triage for suspicious messages and screenshots.</p>
          <div className="footerSafety">
            <InterfaceIcon name="shield" />
            <div><strong>Educational prototype · Synthetic evidence only</strong><span>Do not enter real personal, banking or victim information.</span></div>
          </div>
        </div>
        <div className="footerLinkGrid">
          <nav aria-label="Project" className="footerNav">
            <span>Project</span>
            <Link href="/analyze">Analyze</Link>
            <Link href="/relationships">Relationships</Link>
            <Link href="/research">Research</Link>
            <Link href="/guide">Run guide</Link>
          </nav>
          <nav aria-label="Reach out" className="footerNav">
            <span>Reach out</span>
            {CONTACTS.map(([label, href]) => <a key={label} href={href} target="_blank" rel="noreferrer">{label}</a>)}
            <a href="https://github.com/GautamBytes/fraudlens-bharat-phase-1" target="_blank" rel="noreferrer">Source repository</a>
          </nav>
        </div>
      </div>
      <div className="footerMeta"><span>Human review remains mandatory.</span><span>Built by Gautam Manchandani · 2026</span></div>
    </footer>
  );
}
import Link from "next/link";

import { InterfaceIcon } from "./interface-primitives";
