# Professor Testing Guide

This guide provides two safe ways to evaluate the complete Phase 1 + Phase 2
FraudLens Bharat capstone. The hosted path takes a few minutes and requires no
installation. The Docker path reproduces the full web, API, model, OCR, and
relationship stack locally.

The classifier evidence is based on a 64-row synthetic, fraud-only bootstrap.
Use synthetic data only during evaluation. The tool is a research prototype,
not a production fraud detector or a substitute for bank, police, or National
Cyber Crime Reporting Portal decisions.

## Hosted professor evaluation

The project owner supplies one Vercel URL. Open it in a current Chrome, Edge,
Firefox, or Safari browser. Vercel serves the Next.js interface and proxies
requests to the containerized FastAPI service. The server-only
`FRAUDLENS_API_URL` and `FRAUDLENS_DEMO_API_KEY` are never sent to the browser.

1. On **Overview**, wait for **Engine ready**. A free Render service can take
   roughly one minute to wake after inactivity. Use **Retry** if requested.
2. Open **Analyze**. Run a prepared synthetic message and verify that category,
   confidence, risk signals, masked entities, explanation, and complaint draft
   appear. Storage starts off.
3. Switch to **Screenshot** and use a clear synthetic PNG or JPEG under 4 MB.
   Source image bytes are processed in memory and not retained.
4. Open **Relationships**, choose **Build synthetic link**, and verify that two
   cases connect through a masked repeated entity. The demo clears earlier
   synthetic cases before building its controlled example.
5. Open **Research**. Confirm the experimental character candidate and deployed
   calibrated runtime are separate, and read the eight-row evidence boundary.
6. Open **Run guide** to review the safety and decision-support limitations.

Public service checks are available directly on the backend at `/health`
(liveness) and `/ready` (model and case-store readiness). Data endpoints require
the private demo key and should not be called directly by a professor.

### Reset demo data

On **Relationships**, choose **Clear**. This calls the authenticated same-origin
gateway and deletes the retained synthetic cases. Render free-tier storage is
ephemeral and can also reset when the service restarts.

## Complete local Docker evaluation

Prerequisites: Git and Docker Desktop (or Docker Engine with Compose v2).

```bash
git clone https://github.com/GautamBytes/fraudlens-bharat-phase-1.git
cd fraudlens-bharat-phase-1
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value in `.env` as `FRAUDLENS_HMAC_SECRET`. For loopback-only
evaluation, `FRAUDLENS_DEMO_API_KEY` may remain empty. Then run:

```bash
docker compose config --quiet
docker compose up --build
```

Open `http://127.0.0.1:3000`. The API remains available on
`http://127.0.0.1:8000`; verify it in another terminal:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/ready
```

The Docker path includes English and Hindi Tesseract OCR. The named volume
retains only cases for which storage was explicitly enabled. Stop the project
without deleting that volume:

```bash
docker compose down
```

Use `docker compose down -v` only when intentionally deleting all local demo
case data.

## Split development run

This path is useful for inspecting source changes without rebuilding images.
It requires Python 3.10+, Node.js 22+, and Tesseract with `eng` and `hin` data.

Terminal 1:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install -e . --no-deps
FRAUDLENS_ALLOWED_HOSTS=localhost,127.0.0.1 \
  uvicorn fraudlens.api:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd web
cp .env.example .env.local
npm ci
npm run dev
```

Open `http://127.0.0.1:3000`.

## Verification commands

Python implementation and evidence:

```bash
PYTHONPATH=src python -m pytest -q
```

Web implementation:

```bash
cd web
npm ci
npm test -- --run
npm run lint
npm run typecheck
npm run build
```

## Troubleshooting

- **Engine waking:** wait one minute and retry. This is expected on free hosted
  infrastructure after inactivity.
- **Engine unavailable:** use the Docker path; it is the complete offline
  fallback and does not depend on Render or Vercel.
- **Screenshot rejected:** use PNG/JPEG under 4 MB with readable text. The
  direct Python API allows up to 5 MiB, but the hosted web boundary is smaller.
- **No relationship appears:** choose **Build synthetic link** rather than
  entering unrelated examples. Only repeated masked entities across explicitly
  retained cases form edges.
- **Port already in use:** stop the conflicting local service or adjust the
  loopback port mapping in `compose.yaml`.

## Expected assessment boundary

Successful operation demonstrates an end-to-end explainable workflow: text and
screenshot intake, eight-class calibrated triage with abstention, entity and
risk extraction, complaint drafting, consent-based retention, privacy-safe
relationship analysis, and reproducible research evidence. It does not prove
population-level accuracy, legitimate-message discrimination, production
scalability, or real-world investigative efficacy.
