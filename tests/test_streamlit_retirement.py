from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


ACTIVE_DOCUMENTS = (
    "README.md",
    "docs/installation_guide.md",
    "docs/user_manual.md",
    "docs/professor_testing_guide.md",
    "docs/deployment_guide.md",
    "docs/test_cases.md",
    "docs/release_checklist.md",
    "docs/final_capstone_report.md",
    "docs/phase2_research_report.md",
    "docs/literature_review.md",
    "docs/comparative_analysis.md",
    "docs/evaluation_plan.md",
    "docs/presentation/demo_video_runbook.md",
    "outputs/screenshots/README.md",
)

HISTORICAL_DOCUMENTS = (
    "docs/phase1_report.md",
    "docs/weekly_progress.md",
)

RETIREMENT_NOTE = (
    "Current-scope note (2026-08-10): Phase 1 used a Streamlit demonstration "
    "interface. That interface is retired; the supported final product uses the "
    "Next.js website and FastAPI."
)


def test_streamlit_is_absent_from_the_active_runtime():
    for relative_path in (
        "src/fraudlens/dashboard.py",
        "src/fraudlens/dashboard_workflow.py",
        "src/fraudlens/graph_dashboard.py",
    ):
        assert not (ROOT / relative_path).exists(), relative_path

    for relative_path in (
        "requirements.txt",
        "requirements.lock",
        "requirements-runtime.lock",
        "Dockerfile",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8").lower()
        assert "streamlit" not in text, relative_path

    for source in (ROOT / "src" / "fraudlens").glob("*.py"):
        assert "streamlit" not in source.read_text(encoding="utf-8").lower(), source

    for relative_path in (
        "outputs/screenshots/dashboard_home.png",
        "outputs/screenshots/dashboard_analysis_result.png",
        "outputs/screenshots/dashboard_otp_demo.png",
        "outputs/screenshots/final_dashboard_home.png",
    ):
        assert not (ROOT / relative_path).exists(), relative_path


def test_active_documentation_supports_only_nextjs_and_fastapi():
    for relative_path in ACTIVE_DOCUMENTS:
        text = (ROOT / relative_path).read_text(encoding="utf-8").lower()
        assert "streamlit" not in text, relative_path
        assert "streamlit run" not in text, relative_path
        assert "legacy streamlit dashboard retained" not in text, relative_path

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "modern Next.js professor website" in readme
    assert "FastAPI backend" in readme
    for relative_path in HISTORICAL_DOCUMENTS:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert RETIREMENT_NOTE in text, relative_path
        assert "streamlit run" not in text.lower(), relative_path

    manual = (ROOT / "docs/user_manual.md").read_text(encoding="utf-8")
    inventory = (ROOT / "docs/test_cases.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/presentation/demo_video_runbook.md").read_text(
        encoding="utf-8"
    )
    documentation = "\n".join((manual, inventory, runbook))

    for expected in (
        "Store this synthetic analysis",
        "Fake KYC",
        "Courier hold",
        "Digital arrest",
        "Investment trap",
        "4,000,000 bytes (4 MB)",
        "Analyze",
        "Relationships",
        "Message text",
        "Screenshot",
        "Analyze message",
        "Analyze screenshot",
        "Build synthetic link",
        "clears earlier synthetic cases and seeds the synthetic KYC and courier cases",
        "Refresh",
    ):
        assert expected in documentation

    assert "Store this analysis locally" not in documentation
    assert "Fake KYC SMS" not in documentation
