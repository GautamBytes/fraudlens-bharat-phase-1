import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_professor_web_deployment_contract_is_documented():
    guide = (ROOT / "docs/professor_testing_guide.md").read_text(encoding="utf-8")
    for phrase in (
        "Hosted professor evaluation",
        "docker compose up --build",
        "FRAUDLENS_API_URL",
        "FRAUDLENS_DEMO_API_KEY",
        "synthetic data only",
        "Reset demo data",
        "/health",
        "/ready",
    ):
        assert phrase in guide


def test_render_blueprint_uses_the_hardened_container_and_secrets():
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    service = blueprint["services"][0]
    assert service["type"] == "web"
    assert service["runtime"] == "docker"
    assert service["healthCheckPath"] == "/ready"
    env = {item["key"]: item for item in service["envVars"]}
    assert env["FRAUDLENS_HMAC_SECRET"]["generateValue"] is True
    assert env["FRAUDLENS_DEMO_API_KEY"]["generateValue"] is True
    assert env["FRAUDLENS_STORE_CASES"]["value"] == "false"
    assert env["FRAUDLENS_ALLOWED_HOSTS"]["value"] == (
        "localhost,127.0.0.1,fraudlens-bharat-api.onrender.com"
    )


def test_vercel_and_compose_keep_backend_secrets_server_side():
    vercel = (ROOT / "web/vercel.json").read_text(encoding="utf-8")
    web_env = (ROOT / "web/.env.example").read_text(encoding="utf-8")
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    assert '"framework": "nextjs"' in vercel
    assert '"maxDuration": 60' in vercel
    assert "FRAUDLENS_API_URL=" in web_env
    assert "FRAUDLENS_DEMO_API_KEY=" in web_env
    assert "NEXT_PUBLIC_FRAUDLENS" not in web_env
    assert "web" in compose["services"]
    assert compose["services"]["web"]["ports"] == ["127.0.0.1:3000:3000"]
    assert compose["services"]["web"]["environment"]["FRAUDLENS_API_URL"] == "http://api:8000"
    cases_route = (ROOT / "web/src/app/api/cases/route.ts").read_text(encoding="utf-8")
    assert "export async function GET" not in cases_route
    assert '"/cases?confirm=true"' in cases_route


def test_ci_verifies_the_web_application():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for command in ("npm ci", "npm test -- --run", "npm run lint", "npm run typecheck", "npm run build"):
        assert command in workflow
    assert "working-directory: web" in workflow


def test_web_research_snapshot_matches_committed_evidence():
    snapshot = json.loads(
        (ROOT / "web/src/lib/research-snapshot.json").read_text(encoding="utf-8")
    )
    evidence = json.loads(
        (ROOT / "outputs/presentation/final_evidence.json").read_text(encoding="utf-8")
    )
    assert snapshot["dataset"] == {
        key: evidence["dataset"][key]
        for key in ("rows", "test_rows", "synthetic_only", "legitimate_label_present")
    }
    candidates = {item["model"]: item for item in evidence["research_candidates"]}
    for model, metrics in snapshot["models"].items():
        source = evidence["deployed_runtime"] if model == "deployed_runtime" else candidates[model]
        for key, value in metrics.items():
            if key == "artifact_bytes":
                artifact_names = (
                    "baseline_classifier.joblib",
                    "vectorizer.joblib",
                    "label_encoder.joblib",
                )
                assert value == sum((ROOT / "models" / name).stat().st_size for name in artifact_names)
            else:
                assert value == source[key]
