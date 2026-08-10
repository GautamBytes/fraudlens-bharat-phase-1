import type { ReactNode } from "react";

function Step({ number, title, children }: { number: string; title: string; children: ReactNode }) {
  return <article className="guideStep"><span>{number}</span><div><h3>{title}</h3>{children}</div></article>;
}

function Command({ children }: { children: string }) {
  return <pre tabIndex={0}><code>{children}</code></pre>;
}

export function ProfessorGuide() {
  return (
    <div className="guideStack">
      <section className="guidePath hostedPath" id="hosted">
        <p className="eyebrow">No installation</p><h2>Fastest: hosted evaluation</h2>
        <p>Open the published Vercel URL. Its server securely calls the containerized Python engine; the private key never reaches the browser.</p>
        <div className="guideSteps">
          <Step number="01" title="Open the project"><p>Start on Evaluate. If the first hosted request reports temporary unavailability after inactivity, wait about a minute and retry the action.</p></Step>
          <Step number="02" title="Run prepared evidence"><p>Analyze synthetic text or a screenshot, then inspect confidence, signals and the draft.</p></Step>
          <Step number="03" title="Inspect a campaign"><p>Build the synthetic relationship and confirm the repeated value is masked.</p></Step>
          <Step number="04" title="Audit the claims"><p>Compare research and runtime models, then read the evidence boundary.</p></Step>
        </div>
      </section>

      <section className="guidePath dockerPath" id="docker-run">
        <p className="eyebrow">Full reproducibility</p><h2>Complete: Docker evaluation</h2>
        <p>This path includes the web UI, FastAPI, calibrated model, SQLite case store, and English/Hindi Tesseract OCR.</p>
        <Command>{"cp .env.example .env\ndocker compose up --build"}</Command>
        <p>Set a strong <code>FRAUDLENS_HMAC_SECRET</code>, then open <code>http://localhost:3000</code>. Stop with <code>docker compose down</code>; add <code>-v</code> only when intentionally deleting demo data.</p>
      </section>

      <section className="researchSection" id="development">
        <div className="sectionIntro"><p className="eyebrow">Source-level inspection</p><h2>Split development run</h2></div>
        <div className="commandGrid"><article><h3>1 · Python API</h3><Command>{"python3 -m venv .venv\nsource .venv/bin/activate\npip install --require-hashes -r requirements.lock\npip install -e . --no-deps\nuvicorn fraudlens.api:app --host 127.0.0.1 --port 8000"}</Command></article><article><h3>2 · Next.js website</h3><Command>{"cd web\ncp .env.example .env.local\nnpm ci\nnpm run dev"}</Command></article></div>
        <p className="guideNote"><code>FRAUDLENS_API_URL</code> points the Next.js server to FastAPI. <code>FRAUDLENS_DEMO_API_KEY</code> is optional on loopback and must match at both boundaries when enabled. Never use a <code>NEXT_PUBLIC_</code> prefix for either value.</p>
      </section>

      <section className="researchSection" id="verification">
        <div className="sectionIntro"><p className="eyebrow">Verification</p><h2>Prove the stack before assessment</h2></div>
        <div className="verificationGrid"><article><h3>Service checks</h3><Command>{"curl --fail http://127.0.0.1:8000/health\ncurl --fail http://127.0.0.1:8000/ready"}</Command></article><article><h3>Python tests</h3><Command>{"PYTHONPATH=src python -m pytest -q"}</Command></article><article><h3>Web tests</h3><Command>{"cd web\nnpm test -- --run\nnpm run lint\nnpm run typecheck\nnpm run build"}</Command></article></div>
      </section>

      <section className="guideChecklist" id="failure-states">
        <div className="sectionIntro"><p className="eyebrow">Failure-safe operation</p><h2>Know what each state means</h2></div>
        <ul><li>If a hosted request is temporarily unavailable after inactivity, wait about a minute and retry the action; no state-changing request repeats automatically.</li><li>Hosted storage is ephemeral. Use Reset demo data / Clear after the relationship exercise.</li><li>Use synthetic examples only; never submit a real victim message or personal screenshot.</li><li>Uploaded image bytes are analyzed in memory and are not retained.</li><li>If hosting is unavailable, Docker is the complete offline fallback.</li><li>The draft supports human review; it does not replace bank, police, or cybercrime reporting decisions.</li></ul>
      </section>
    </div>
  );
}
