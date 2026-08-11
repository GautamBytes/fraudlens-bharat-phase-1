import type { Metadata } from "next";

import { SignInForm } from "@/components/sign-in-form";
import { safeReturnPath } from "@/lib/auth-policy";

export const metadata: Metadata = {
  title: "Professor access",
  description: "Sign in to the protected FraudLens Bharat evaluation workspace.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ returnTo?: string }>;
}) {
  const query = await searchParams;
  const returnTo = safeReturnPath(query.returnTo ?? null);

  return (
    <main className="authPage">
      <section className="authPanel" aria-labelledby="professor-access-title">
        <div className="authIntro">
          <span className="eyebrow">Controlled evaluation workspace</span>
          <h1 id="professor-access-title">Professor access</h1>
          <p>
            Sign in with the account provided by the project author to test analysis,
            screenshot OCR, research evidence, and masked relationships.
          </p>
        </div>
        <SignInForm returnTo={returnTo} />
        <div className="authBoundaryNote">
          <strong>Synthetic evidence only</strong>
          <span>Do not enter real personal, banking, or victim information.</span>
        </div>
      </section>
      <aside className="authSignal" aria-label="Protected project capabilities">
        <span className="eyebrow">Authenticated review</span>
        <h2>One account. Complete project access.</h2>
        <ol>
          <li><span>01</span>Analyze suspicious messages</li>
          <li><span>02</span>Run bounded screenshot OCR</li>
          <li><span>03</span>Inspect masked relationship evidence</li>
          <li><span>04</span>Review reproducible research results</li>
        </ol>
      </aside>
    </main>
  );
}
