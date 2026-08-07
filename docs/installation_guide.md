# Installation Guide

## Prerequisites

- Python 3.10 or higher
- macOS/Linux/Windows terminal
- Internet access for first-time package installation

## Runtime installation

Use this installation for the API, dashboard, or training command.

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

## Run Dashboard

```bash
streamlit run src/fraudlens/dashboard.py
```

## Run Tests

```bash
pytest
```
