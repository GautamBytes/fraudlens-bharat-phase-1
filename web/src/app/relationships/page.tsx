import type { Metadata } from "next";
import { RelationshipWorkbench } from "@/components/relationship-workbench";

export const metadata: Metadata = { title: "Relationships" };
export default function RelationshipsPage() { return <main className="pageFrame"><header className="pageHeader"><p className="eyebrow">Phase 2 · relationship intelligence</p><h1>See when separate reports share the same masked infrastructure.</h1><p>Build a controlled two-case example, inspect its graph, then verify the same evidence in a table.</p></header><RelationshipWorkbench initialGraph={null} /></main>; }
