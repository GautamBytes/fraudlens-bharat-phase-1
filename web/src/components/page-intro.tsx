import type { ReactNode } from "react";

export type PageIntroProps = {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
};

export function PageIntro({ eyebrow, title, description, actions }: PageIntroProps) {
  return (
    <header className="pageIntro">
      <div className="pageIntroCopy">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      <div className="pageIntroAside">
        <p>{description}</p>
        {actions && <div className="pageIntroActions">{actions}</div>}
      </div>
    </header>
  );
}
