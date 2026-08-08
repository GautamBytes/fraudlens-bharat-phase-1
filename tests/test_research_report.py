from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase2_research_report_has_complete_academic_structure():
    report = _read("docs/phase2_research_report.md")

    for heading in (
        "# FraudLens Bharat Phase 2 Research Report",
        "## Abstract",
        "## 1. Introduction",
        "## 2. Research Questions And Hypotheses",
        "## 3. Literature Selection Method",
        "## 4. Existing Solution Families",
        "## 5. Research Gap And Proposed Contribution",
        "## 6. Dataset And Ethics",
        "## 7. Experimental Methodology",
        "## 8. Classification Results",
        "## 9. Robustness And Ablation Results",
        "## 10. Full-System Evaluation Framework",
        "## 11. Statistical Interpretation",
        "## 12. Explainability, Privacy, And Deployment",
        "## 13. Threats To Validity",
        "## 14. Conclusion",
        "## Reproduction Commands",
    ):
        assert heading in report


def test_report_separates_published_results_from_same_dataset_results():
    report = _read("docs/phase2_research_report.md")

    for expected in (
        "74.41%",
        "71.49%",
        "97%",
        "different dataset and task",
        "not a shared leaderboard",
        "64 synthetic",
        "eight-row frozen test",
        "no legitimate",
        "does not establish production accuracy",
    ):
        assert expected in report


def test_report_contains_exact_reproducible_results_and_failure_analysis():
    report = _read("docs/phase2_research_report.md")

    for expected in (
        "character_tfidf_logistic_regression",
        "0.7500",
        "0.6667",
        "0.7412",
        "word_tfidf_logistic_regression",
        "0.3750",
        "0.3333",
        "digital_arrest",
        "otp_phishing",
        "OCR confusion",
        "+0.3333",
        "0.0498",
        "0.4084",
    ):
        assert expected in report


def test_methodology_explains_each_metric_and_leakage_control():
    methodology = _read("docs/research_methodology.md")

    for expected in (
        "Macro-F1",
        "Balanced accuracy",
        "Matthews correlation coefficient",
        "Expected calibration error",
        "Brier score",
        "Coverage",
        "Accepted accuracy",
        "paired bootstrap",
        "95% confidence interval",
        "template_group",
        "provenance_id",
        "train",
        "validation",
        "test",
        "200 examples per label",
    ):
        assert expected in methodology


def test_readme_and_comparison_point_to_research_evidence():
    readme = _read("README.md")
    comparison = _read("docs/comparative_analysis.md")

    for expected in (
        "Research Benchmark",
        "docs/phase2_research_report.md",
        "outputs/research/classification_summary.csv",
        "outputs/research/ablation_summary.csv",
        "full diagnostic JSON is generated locally",
    ):
        assert expected in readme
    assert "Phase 2 research benchmark" in comparison
    assert "same frozen split" in comparison


def test_ci_regenerates_every_canonical_research_artifact():
    workflow = _read(".github/workflows/ci.yml")

    for expected in (
        "Verify deterministic research evidence",
        "fraudlens.research_dataset",
        "fraudlens.research_benchmark",
        "fraudlens.research_robustness",
        "dataset_audit.json",
        "classification_benchmark.json",
        "classification_summary.csv",
        "robustness_benchmark.json",
        "ablation_summary.csv",
        '"$research_tmp/first/$artifact" "$research_tmp/second/$artifact"',
    ):
        assert expected in workflow


def test_verbose_diagnostic_json_is_generated_but_not_tracked():
    ignore = _read(".gitignore")

    assert "outputs/research/classification_benchmark.json" in ignore
    assert "outputs/research/robustness_benchmark.json" in ignore


def test_hingbert_reference_uses_the_official_acl_authors():
    references = _read("docs/references.md")
    reference = next(line for line in references.splitlines() if line.startswith("[14]"))

    assert reference.startswith("[14] R. Nayak and R. Joshi")
    assert "R. R. Shah" not in reference
