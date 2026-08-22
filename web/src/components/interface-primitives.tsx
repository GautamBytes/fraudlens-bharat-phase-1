import type { ReactNode, SVGProps } from "react";

export type InterfaceIconName = "arrow" | "menu" | "close" | "shield" | "spark" | "copy" | "check" | "external";

const PATHS: Record<InterfaceIconName, ReactNode> = {
  arrow: <><path d="M5 12h14" /><path d="m14 7 5 5-5 5" /></>,
  menu: <><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" /></>,
  close: <><path d="m6 6 12 12" /><path d="m18 6-12 12" /></>,
  shield: <><path d="M12 3 5.5 5.8v5.1c0 4.2 2.6 7.7 6.5 9.1 3.9-1.4 6.5-4.9 6.5-9.1V5.8L12 3Z" /><path d="m9.3 11.8 1.8 1.8 3.7-4" /></>,
  spark: <><path d="m12 3 1.2 4.1L17 9l-3.8 1.9L12 15l-1.2-4.1L7 9l3.8-1.9L12 3Z" /><path d="m18 15 .7 2.3L21 18.5l-2.3 1.2L18 22l-.7-2.3-2.3-1.2 2.3-1.2L18 15Z" /></>,
  copy: <><rect x="8" y="8" width="11" height="11" rx="2" /><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  external: <><path d="M14 5h5v5" /><path d="m11 13 8-8" /><path d="M19 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" /></>,
};

export function InterfaceIcon({ name, ...props }: { name: InterfaceIconName } & SVGProps<SVGSVGElement>) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      {PATHS[name]}
    </svg>
  );
}

export function StatusPill({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "safe" | "warning" | "danger" }) {
  const toneClass = tone.charAt(0).toUpperCase() + tone.slice(1);
  return <span className={`statusPill statusPill${toneClass}`}>{children}</span>;
}
