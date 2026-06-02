# Installation Guide

## Prerequisites

- Python 3.9 or higher
- macOS/Linux/Windows terminal
- Internet access for first-time package installation

## Steps

```bash
cd "/Users/gautammanch/capstone-project(phase-1)"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

On Windows PowerShell:

```powershell
cd "C:\path\to\capstone-project(phase-1)"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
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

