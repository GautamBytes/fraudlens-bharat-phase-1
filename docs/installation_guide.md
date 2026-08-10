# Installation Guide

## Prerequisites

- Python 3.10 or higher
- macOS/Linux/Windows terminal
- Internet access for first-time package installation
- Tesseract OCR with English and Hindi language data for screenshot analysis

## Runtime installation

Install Tesseract before using screenshot analysis.

On macOS with Homebrew:

```bash
brew install tesseract tesseract-lang
```

On Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
```

Confirm that both OCR languages are installed:

```bash
tesseract --list-langs
```

The output must include `eng` and `hin`. Next, install the Python runtime for
the FastAPI service or training command.

```bash
cd /path/to/fraudlens-bharat
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
```

On Windows PowerShell:

```powershell
cd "C:\path\to\capstone-project(phase-1)"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps
```

## Contributor and test installation

After activating the virtual environment, contributors should install the
development requirements, which include the runtime dependencies and `pytest`:

```bash
pip install -r requirements-dev.txt
pip install -e . --no-deps
```

## Train Model

```bash
python -m fraudlens.model_training
```

## Generate Demo Outputs

```bash
python -m fraudlens.generate_demo_cases
```

## Run API

```bash
uvicorn fraudlens.api:app --reload
```

`--reload` is for local development only. The production container runs without
the reloader and disables Uvicorn's raw access log in favor of the application's
redacted structured request events.

Open:

```text
http://127.0.0.1:8000/docs
```

Check process liveness with `GET /health`. Check application readiness,
including the initialized SQLite case store, with `GET /ready`.

Send screenshots as a raw request body, not as multipart form data:

```bash
curl -X POST "http://127.0.0.1:8000/analyze-image?store_case=false" \
  -H "Content-Type: image/png" \
  --data-binary @screenshot.png
```

The endpoint accepts PNG and JPEG files up to 5 MiB. Each image must be no
larger than 4096 x 4096 and 16,000,000 pixels. OCR uses English and Hindi
language data (`eng+hin`).

## Run Tests

```bash
pytest
```

## Run the hardened containers

Docker Compose runs the FastAPI service and Next.js website as non-root users,
binds both ports to loopback, keeps the container filesystem read-only, and
mounts a persistent data volume for SQLite.

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# Paste that unique output after FRAUDLENS_HMAC_SECRET= in .env.
docker compose config --quiet
docker compose up --build --detach
curl --fail http://127.0.0.1:8000/ready
```

Open `http://127.0.0.1:3000` for the website. The message tab maps to
`POST /analyze`, the screenshot tab maps to `POST /analyze-image`, and
`/relationships` presents the bounded evidence from `GET /graph`. For API-only
use, run `uvicorn fraudlens.api:app --host 127.0.0.1 --port 8000`. Follow
`docs/deployment_guide.md` for exposure, backups, monitoring, and rollback.
