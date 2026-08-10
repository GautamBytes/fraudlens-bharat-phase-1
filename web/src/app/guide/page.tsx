import type { Metadata } from "next";
import { ProfessorGuide } from "@/components/professor-guide";

export const metadata: Metadata = { title: "Run guide" };
export default function GuidePage() { return <main className="pageFrame"><header className="pageHeader"><p className="eyebrow">Professor evaluation guide</p><h1>Test the project in minutes—or reproduce the complete stack.</h1><p>Choose the hosted path for convenience or Docker for the complete local environment.</p></header><ProfessorGuide /></main>; }
