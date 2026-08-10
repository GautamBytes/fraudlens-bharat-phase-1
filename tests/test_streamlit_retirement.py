from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
