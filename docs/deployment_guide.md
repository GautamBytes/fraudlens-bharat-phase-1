# Deployment Guide

## Supported release boundary

The supplied Compose deployment is intended for a single trusted host, a
capstone demonstration, or a private service behind an authenticated gateway.
It uses SQLite and deliberately binds the API and dashboard to loopback. The
application does not include user authentication, authorization, or distributed
rate limiting. This deployment does not establish production accuracy. Do not
expose either port directly to the public internet.

For remote access, place an authenticated gateway or reverse proxy in front,
terminate TLS there, restrict network access, and set
`FRAUDLENS_ALLOWED_HOSTS` to the exact external host names. The software and
container controls do not establish production accuracy; the committed
evaluation remains a small synthetic bootstrap.

## Configure and launch

1. Copy `.env.example` to `.env` and keep the resulting file out of version
   control with restrictive file permissions.
2. Generate a unique secret with
   `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` and set it as
   `FRAUDLENS_HMAC_SECRET`.
3. Keep `FRAUDLENS_ALLOWED_HOSTS=localhost,127.0.0.1` for the default local
   deployment. Use only explicit host names; wildcards are rejected.
4. Validate and launch:

```bash
docker compose config --quiet
docker compose up --build --detach
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/ready
```

The image is based on a digest-pinned Python 3.11.15 image and a
hash-validated production dependency lock. API and dashboard processes run as
the non-root UID 10001. Compose uses a read-only root filesystem, drops all
Linux capabilities, sets `no-new-privileges`, and gives only `/tmp` and the
`/data` volume write access. English and Hindi Tesseract data are installed.

Case storage remains off by default. Explicit user consent is still required
to retain analysis text, and source screenshot bytes are never retained.

## Health and logs

- `/health` is a liveness signal and does not probe dependencies.
- `/ready` checks the initialized SQLite case store and returns generic `503`
  output if storage is unavailable.
- `X-Request-ID` correlates a response with the safe structured request event.
- Request events include only request ID, method, route template, and status.
  They exclude raw paths, query strings, headers, client addresses, message
  text, OCR text, notes, and entity values.

Use `docker compose ps` for service health and `docker compose logs api` for
startup and request-event diagnostics. Treat logs as operational data even
though application fields are minimized.

## SQLite backup and retention

The named `fraudlens-data` volume contains `/data/cases.sqlite3`. Retention
purges expired raw case records during normal storage operations and startup.
Schedule a backup more frequently than the acceptable recovery-point window.

Create a transactionally consistent backup with Python's SQLite backup API,
then copy it to a protected host directory:

```bash
mkdir -p backups
chmod 700 backups
docker compose exec -T api python -c "import sqlite3; source=sqlite3.connect('/data/cases.sqlite3'); target=sqlite3.connect('/data/cases.backup.sqlite3'); source.backup(target); target.close(); source.close()"
docker compose cp api:/data/cases.backup.sqlite3 backups/cases.backup.sqlite3
chmod 600 backups/cases.backup.sqlite3
```

Test backups separately. For a restore, stop both services, retain a copy of
the current volume, validate the selected backup with SQLite, replace the
database only through an approved operator procedure, then restart and require
`/ready` to pass before serving traffic. Never use `docker compose down -v`
during a normal update because it deletes the named data volume.

Changing the HMAC secret is a privacy-sensitive migration, not a routine
restart. A secret rotation changes future opaque entity IDs, so relationships
created before and after secret rotation will not join unless retained entity
links are deliberately re-keyed. Keep secrets in a secret manager and define a
rotation/backup procedure before external deployment.

## Update and rollback

Before an update, record the current image digest, take and verify a database
backup, and confirm the new commit's CI `container-smoke` job is green. Deploy
the new immutable tag, then check `/ready`, a non-sensitive analysis, dashboard
load, and logs.

For an application rollback, restore the previous immutable image tag and run
`docker compose up --detach --no-build`. Recheck `/health` and `/ready`. Database
initialization performs safe migrations and retention purges, so do not assume
an application rollback reverses data changes. Use the separately verified
backup only when the rollback decision explicitly requires a database restore.

Escalate and stop serving requests if readiness remains unavailable, artifact
integrity falls back unexpectedly, stored-case deletion fails, or any sensitive
request value appears in logs.
