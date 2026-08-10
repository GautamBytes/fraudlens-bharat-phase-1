import type { Metadata } from "next";

import { AnalysisWorkbench } from "@/components/analysis-workbench";
import { PageIntro } from "@/components/page-intro";

export const metadata: Metadata = { title: "Analyze evidence" };

export default function AnalyzePage() {
  return (
    <main className="pageContent analysisPage">
      <PageIntro
        eyebrow="Live workflow"
        title="Analyze fraud evidence"
        description="Use a prepared message or synthetic screenshot. The same calibrated Python service powers both paths."
      />
      <AnalysisWorkbench />
    </main>
  );
}
