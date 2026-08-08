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
the API, dashboard, or training command.

```bash
cd "/Users/gautammanch/capstone-project(phase-1)"
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

Open:

```text
http://127.0.0.1:8000/docs
```

Send screenshots as a raw request body, not as multipart form data:

```bash
curl -X POST "http://127.0.0.1:8000/analyze-image?store_case=false" \
  -H "Content-Type: image/png" \
  --data-binary @screenshot.png
```

The endpoint accepts PNG and JPEG files up to 5 MiB. Each image must be no
larger than 4096 x 4096 and 16,000,000 pixels. OCR uses English and Hindi
language data (`eng+hin`).

## Run Dashboard

```bash
streamlit run src/fraudlens/dashboard.py
```

## Run Tests

```bash
pytest
```
