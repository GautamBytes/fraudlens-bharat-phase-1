# Deployment Guide

## Supported release boundary

The supplied Compose deployment is intended for a single trusted host, a
capstone demonstration, or a private service behind an authenticated gateway.
It uses SQLite and deliberately binds the API and modern Next.js website to
loopback. The hosted capstone demo uses a separate Vercel website and Render
API protected by a private demo key. The website uses Better Auth with durable
PostgreSQL, one pre-provisioned reviewer account, secure sessions, disabled
public sign-up, and database-backed login rate limiting. This remains a
controlled capstone deployment rather than a multi-user production service,
and it does not establish production accuracy.
Do not expose the local API port directly to the public internet.

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
   `FRAUDLENS_HMAC_SECRET`. Generate independent values for
   `FRAUDLENS_AUTH_DB_PASSWORD` and `BETTER_AUTH_SECRET`.
3. Keep `FRAUDLENS_ALLOWED_HOSTS=localhost,127.0.0.1,api` for the default local
   deployment. `api` is the internal Compose service host. Use only explicit
   host names; wildcards are rejected.
4. Start `auth-db`, configure `web/.env` from `web/.env.example`, then run
   `npm run auth:migrate` and `npm run auth:create-professor` from `web/`.
   Use the same database password and Better Auth secret in both environment
   files, then remove the provisioning-only reviewer credentials from
   `web/.env`. The complete command sequence is in
   `professor_testing_guide.md`.
5. Validate and launch:

```bash
docker compose config --quiet
docker compose up --build --detach
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/ready
```

The Python image is based on digest-pinned Python 3.11.15 and a hash-validated
runtime lock. The web image uses Node 22 and a standalone Next.js production
build. Both services run as non-root UID 10001. Compose uses read-only root
filesystems, drops all Linux capabilities, sets `no-new-privileges`, and gives
only `/tmp` and the API `/data` volume write access. English and Hindi
Tesseract data are installed in the API image.

## Hosted capstone deployment

`render.yaml` provisions the hardened API container with `/ready` health
checks and generated secrets. After Render creates the service, confirm its
final hostname matches `FRAUDLENS_ALLOWED_HOSTS`; update that exact value if
Render assigned a suffix, while retaining the loopback entries used by health
checks. Copy the generated `FRAUDLENS_DEMO_API_KEY` securely.

Create a Vercel project with **Root Directory** set to `web`, then set the
server-only environment values `FRAUDLENS_API_URL` (the HTTPS Render origin)
and `FRAUDLENS_DEMO_API_KEY` (the matching secret). Do not add `NEXT_PUBLIC_`
to either name. The browser calls only same-origin `/api/*` handlers, so the
backend address and key remain on the Vercel server boundary. The repository's
`web/vercel.json` selects the Next.js framework using Vercel's current static
configuration schema and gives the bounded proxy routes the Hobby tier's
60-second maximum duration. The screenshot proxy aborts upstream work before
that platform deadline.

Attach a durable PostgreSQL database such as Neon and configure `DATABASE_URL`,
`BETTER_AUTH_SECRET` with at least 32 high-entropy characters, and
`BETTER_AUTH_URL=https://fraudlens-bharat.vercel.app` in Vercel. Run
`npm run auth:migrate` against that database, then provision the single
reviewer with `npm run auth:create-professor`. The provisioning email and
password are local command inputs only; do not store them as Vercel variables.
Public sign-up remains disabled in the deployed auth configuration.

The free Render filesystem is ephemeral. This is acceptable for the controlled
professor relationship demo, but it is not a durable evidence store. See
`professor_testing_guide.md` for the expected evaluation and reset sequence.
The public landing page is a project showcase. Functional pages and APIs require
the pre-provisioned professor session. This is controlled reviewer access, not
self-service identity management: there is no public registration, password
reset email, organization model, or real-record workflow. The website does not
proxy the backend case-list or case-detail read endpoints. Use only synthetic
inputs and do not adapt this shared demo for real records.

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
backup, and confirm the new commit's CI web and `container-smoke` jobs are
green. Deploy the new immutable tag, then check `/ready`, a non-sensitive
analysis, website load, and logs.

For an application rollback, restore the previous immutable image tag and run
`docker compose up --detach --no-build`. Recheck `/health` and `/ready`. Database
initialization performs safe migrations and retention purges, so do not assume
an application rollback reverses data changes. Use the separately verified
backup only when the rollback decision explicitly requires a database restore.

Escalate and stop serving requests if readiness remains unavailable, artifact
integrity falls back unexpectedly, stored-case deletion fails, or any sensitive
request value appears in logs.
