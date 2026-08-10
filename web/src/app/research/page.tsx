import type { Metadata } from "next";
import { DocsFrame } from "@/components/docs-frame";
import { PageIntro } from "@/components/page-intro";
import { ResearchEvidence } from "@/components/research-evidence";

export const metadata: Metadata = { title: "Research" };

const INDEX = [
  { href: "#comparison", label: "Model comparison" },
  { href: "#approaches", label: "All approaches" },
  { href: "#parameters", label: "Metric rationale" },
];

const OUTLINE = [
  { href: "#comparison", label: "Candidate and runtime" },
  { href: "#approaches", label: "Same-split results" },
  { href: "#parameters", label: "Why the metrics matter" },
];

export default function ResearchPage() {
  return (
    <main className="pageContent docsPage researchPage">
      <PageIntro
        eyebrow="Research evidence · frozen evaluation"
        title="Measure the gain. Show the boundary."
        description="Every result uses the same internal synthetic split. Candidate selection, deployed behavior, and limitations remain separate."
      />
      <DocsFrame index={INDEX} outline={OUTLINE}><ResearchEvidence /></DocsFrame>
    </main>
  );
}
