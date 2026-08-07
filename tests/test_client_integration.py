from pathlib import Path


SOURCE_ROOT = Path(__file__).parents[1] / "src" / "fraudlens"


def test_dashboard_uses_the_service_with_explicit_opt_in_storage():
    source = (SOURCE_ROOT / "dashboard.py").read_text(encoding="utf-8")

    assert "from fraudlens.api" not in source
    assert "from fraudlens.database import list_cases" not in source
    assert "AnalysisInput" in source
    assert 'st.checkbox("Store this analysis locally", value=False)' in source
    assert "store_case=store_case" in source
    assert '"prediction_model_version"' in source
    assert '"prediction_abstained"' in source
    assert '"stored"' in source


def test_dashboard_history_uses_the_same_configured_store_as_analysis():
    source = (SOURCE_ROOT / "dashboard.py").read_text(encoding="utf-8")

    assert "settings = Settings.from_env()" in source
    assert "DatabaseCaseStore(settings.database_path)" in source
    assert "create_analysis_service(settings=settings, store=case_store)" in source
    assert "case_store.list_cases(limit=10)" in source


def test_demo_case_generation_uses_service_without_persisting_cases():
    source = (SOURCE_ROOT / "generate_demo_cases.py").read_text(encoding="utf-8")

    assert "from fraudlens.api" not in source
    assert "create_analysis_service" in source
    assert "AnalysisInput(text=text, store_case=False)" in source
