import type { Metadata } from "next";
import { DocsFrame } from "@/components/docs-frame";
import { PageIntro } from "@/components/page-intro";
import { ProfessorGuide } from "@/components/professor-guide";

export const metadata: Metadata = { title: "Run guide" };

const INDEX = [
  { href: "#hosted", label: "Hosted evaluation" },
  { href: "#docker-run", label: "Complete local run" },
  { href: "#development", label: "Development run" },
  { href: "#verification", label: "Verification" },
  { href: "#failure-states", label: "Failure states" },
];

const OUTLINE = [
  { href: "#hosted", label: "Fastest path" },
  { href: "#docker-run", label: "Docker commands" },
  { href: "#development", label: "Split services" },
  { href: "#verification", label: "Health and tests" },
  { href: "#failure-states", label: "Safe recovery" },
];

export default function GuidePage() {
  return (
    <main className="pageContent docsPage guidePage">
      <PageIntro
        eyebrow="Professor evaluation guide"
        title="Test it in minutes. Reproduce every layer."
        description="Use the hosted path for a quick review or Docker for the complete local model, OCR, storage, API, and website stack."
      />
      <DocsFrame index={INDEX} outline={OUTLINE}><ProfessorGuide /></DocsFrame>
    </main>
  );
}
