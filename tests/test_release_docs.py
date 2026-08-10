from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_exposes_the_1_0_release_path_and_health_contract():
    readme = _read("README.md")

    for expected in (
        "Release 1.0",
        "docker compose up --build --detach",
        "GET /health",
        "GET /ready",
        "http://127.0.0.1:3000",
        "docs/professor_testing_guide.md",
        "docs/deployment_guide.md",
        "docs/release_checklist.md",
    ):
        assert expected in readme


def test_deployment_guide_covers_security_backup_rollback_and_limits():
    guide = _read("docs/deployment_guide.md")

    for expected in (
        "FRAUDLENS_HMAC_SECRET",
        "FRAUDLENS_ALLOWED_HOSTS",
        "docker compose config --quiet",
        "docker compose up --build --detach",
        "curl --fail http://127.0.0.1:8000/ready",
        "non-root",
        "read-only",
        "TLS",
        "authenticated gateway",
        "SQLite",
        "backup",
        "rollback",
        "secret rotation",
        "does not establish production accuracy",
    ):
        assert expected in guide


def test_release_checklist_requires_evidence_and_green_container_gate():
    checklist = _read("docs/release_checklist.md")

    for expected in (
        "pytest",
        "pip-audit",
        "docker build",
        "container-smoke",
        "eng",
        "hin",
        "no real victim PII",
        "outputs/phase2/evaluation.json",
        "v1.0.0",
        "rollback",
    ):
        assert expected in checklist


def test_test_inventory_contains_final_release_controls():
    inventory = _read("docs/test_cases.md")

    for test_case in range(29, 35):
        assert "TC-{:03d}".format(test_case) in inventory
