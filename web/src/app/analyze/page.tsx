import type { Metadata } from "next";

import { AnalysisWorkbench } from "@/components/analysis-workbench";

export const metadata: Metadata = { title: "Analyze evidence" };

export default function AnalyzePage() {
  return (
    <main className="pageContent">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">Live workflow</p>
          <h1>Analyze fraud evidence</h1>
        </div>
        <p>Use a prepared example or synthetic screenshot. The same Python service powers both paths.</p>
      </header>
      <AnalysisWorkbench />
    </main>
  );
}
