# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

ARG PYTHON_IMAGE=python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3

FROM ${PYTHON_IMAGE} AS dependencies

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:${PATH}

WORKDIR /build
COPY requirements-runtime.lock ./
RUN python -m pip install --only-binary=:all: --require-hashes -r requirements-runtime.lock \
    && python -m pip check \
    && python -m pip uninstall --yes setuptools wheel \
    && python -m pip uninstall --yes pip

FROM ${PYTHON_IMAGE} AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/home/fraudlens \
    PATH=/opt/venv/bin:${PATH} \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRAUDLENS_DB_PATH=/data/cases.sqlite3

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 fraudlens \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/fraudlens fraudlens \
    && install -d -o 10001 -g 10001 /data \
    && python -m pip uninstall --yes setuptools wheel \
    && python -m pip uninstall --yes pip

COPY --from=dependencies /opt/venv /opt/venv

WORKDIR /app
COPY src ./src
COPY models ./models

USER 10001:10001
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3).read()"]

CMD ["uvicorn", "fraudlens.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--limit-concurrency", "100", "--timeout-keep-alive", "5"]
