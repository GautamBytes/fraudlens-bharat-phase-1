# Release 1.0 Checklist

Use this gate for the final `v1.0.0` tag. Do not tag or publish when a required
item is incomplete.

## Evidence and scope

- Confirm no real victim PII is present in tests, examples, screenshots, logs,
  or committed databases.
- Re-read `outputs/phase2/evaluation.json` and `outputs/phase2/summary.txt` and
  preserve their explicit synthetic-data and unmet-data-target limitations.
- Confirm release notes do not claim transformer/GNN functionality, automated
  complaint submission, production accuracy, or a production fraud network.
- Confirm storage defaults off, screenshots are not retained, and graph output
  remains masked and observational.

## Reproducible verification

Run in a clean Python 3.11.15 contributor environment:

```bash
python -m compileall -q src tests
pytest
uvx pip-audit -r requirements.lock
uvx pip-audit -r requirements-runtime.lock
docker build --tag fraudlens-bharat:release .
```

Verify the build-time `python -m pip check` succeeds, the image runs as UID
10001, runtime package managers and pytest are absent, and
`tesseract --list-langs` contains both `eng` and `hin`. Require the
GitHub Actions Python 3.10/3.11.15/3.12 matrix and `container-smoke` job to be
green. That job also verifies readiness, the committed model, Compose policy,
and log redaction.

## Manual acceptance

- Check `/health`, `/ready`, OpenAPI version `1.0.0`, and the dashboard.
- Analyze one synthetic text and one synthetic PNG/JPEG without storage; case
  history must remain empty.
- Repeat with explicit consent; verify history, masked repeated-entity graph,
  single-case deletion, and clear-history confirmation.
- Confirm the response request ID appears in a structured route-template log
  and the submitted synthetic text does not.
- Confirm malformed/oversized images and unavailable OCR return fixed generic
  errors.

## Deployment and rollback readiness

- Generate the production HMAC secret in the target secret manager and use
  explicit allowed hosts.
- Verify the SQLite backup, retention period, free space, TLS/authenticated
  gateway, log access policy, owner, and incident contact.
- Record the previous immutable image digest and rehearse the application
  rollback plus `/ready` verification.
- After merge and green checks, create the `v1.0.0` tag from the reviewed merge
  commit. Preserve the CI evidence and deployment record with the release.
