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
          {CONTACTS.map(([label, href]) => (
            <a key={label} href={href} target="_blank" rel="noreferrer">
              {label}
            </a>
          ))}
        </nav>
      </div>
    </footer>
  );
}
