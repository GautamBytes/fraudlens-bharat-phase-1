import type { Metadata } from "next";
import { ResearchEvidence } from "@/components/research-evidence";

export const metadata: Metadata = { title: "Research" };
export default function ResearchPage() { return <main className="pageFrame"><header className="pageHeader"><p className="eyebrow">Research evidence · frozen evaluation</p><h1>Better means measurable—and honestly bounded.</h1><p>Every result below uses the same internal synthetic split. Candidate selection, deployment behavior, and limitations remain visibly separate.</p></header><ResearchEvidence /></main>; }
