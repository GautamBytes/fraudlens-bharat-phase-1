import type { Metadata } from "next";
import { PageIntro } from "@/components/page-intro";
import { RelationshipWorkbench } from "@/components/relationship-workbench";

export const metadata: Metadata = { title: "Relationships" };

export default function RelationshipsPage() {
  return (
    <main className="pageContent relationshipPage">
      <PageIntro
        eyebrow="Phase 2 · relationship intelligence"
        title="Trace repeated signals across separate reports."
        description="Build a controlled two-case example, inspect its privacy-safe signal map, then verify each observed edge in the table."
      />
      <RelationshipWorkbench initialGraph={null} />
    </main>
  );
}
