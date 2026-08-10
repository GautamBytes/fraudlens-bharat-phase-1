import csv
import html
import json
import posixpath
import re
import subprocess
import sys
import zipfile
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "docs" / "presentation" / "fraudlens-bharat-final-capstone.pptx"
RUNBOOK = ROOT / "docs" / "presentation" / "demo_video_runbook.md"
FINAL_REPORT = ROOT / "docs" / "final_capstone_report.md"
RELEASE_SNAPSHOT = ROOT / "docs" / "presentation" / "release_snapshot.json"


def _deck_slide_text() -> list[str]:
    with zipfile.ZipFile(DECK) as archive:
        slide_names = sorted(
            (
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=lambda name: int(re.search(r"\d+", name).group()),
        )
        return [
            html.unescape(" ".join(
                re.findall(
                    r"<a:t>(.*?)</a:t>",
                    archive.read(name).decode("utf-8"),
                    flags=re.DOTALL,
                )
            ))
            for name in slide_names
        ]


@lru_cache(maxsize=1)
def _collected_test_count() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout + result.stderr)
    assert match is not None, result.stdout + result.stderr
    return int(match.group(1))


@lru_cache(maxsize=1)
def _machine_claims() -> dict[str, str]:
    metrics = json.loads(
        (ROOT / "models" / "metrics.json").read_text(encoding="utf-8")
    )["test"]
    evaluation = json.loads(
        (ROOT / "outputs" / "phase2" / "evaluation.json").read_text(
            encoding="utf-8"
        )
    )["dataset"]
    with (ROOT / "outputs" / "research" / "classification_summary.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        candidates = {row["model"]: row for row in csv.DictReader(handle)}
    character = candidates["character_tfidf_logistic_regression"]
    hybrid = candidates["word_character_tfidf_logistic_regression"]
    assert evaluation["missing_labels"] == ["legitimate"]
    assert not evaluation["phase2_target_met"]
    assert float(character["accuracy"]) == float(hybrid["accuracy"])
    assert float(character["macro_f1"]) == float(hybrid["macro_f1"])
    assert int(character["estimated_model_bytes"]) < int(
        hybrid["estimated_model_bytes"]
    )
    release_snapshot = json.loads(RELEASE_SNAPSHOT.read_text(encoding="utf-8"))
    release_test_count = int(release_snapshot["automated_tests"])
    assert release_snapshot["schema_version"] == 1
    assert _collected_test_count() == release_test_count
    return {
        "test_count": f"{release_test_count} automated tests",
        "dataset": f"{evaluation['rows']} synthetic fraud-only messages",
        "research_accuracy": f"{float(character['accuracy']) * 100:.1f}% accuracy",
        "research_macro_f1": (
            f"{float(character['macro_f1']) * 100:.2f}% Macro-F1"
        ),
        "runtime_accuracy": (
            f"{metrics['overall_accuracy_with_abstentions'] * 100:.1f}% "
            "runtime accuracy"
        ),
        "runtime_coverage": f"{metrics['coverage'] * 100:.1f}% coverage",
    }


def test_final_deck_fills_the_ten_slide_college_template():
    slides = _deck_slide_text()
    text = " ".join(slides)

    assert len(slides) == 10
    assert not (
        ROOT / "docs" / "presentation" / "fraudlens-bharat-phase-1-pitch.pptx"
    ).exists()
    assert not (
        ROOT / "docs" / "presentation" / "final_presentation_script.md"
    ).exists()
    assert not (
        ROOT / "docs" / "presentation" / "presentation_script.md"
    ).exists()
    for title in (
        "Problem Statement",
        "Objectives & Scope",
        "Existing System / Literature Review",
        "Proposed System Architecture",
        "Tools & Technologies",
        "Implementation / Demo",
        "Results & Analysis",
        "Challenges & Limitations",
        "Conclusion & Future Work",
    ):
        assert title in text

    for placeholder in (
        "Capstone Project Title",
        "Team Members",
        "Supervisor Name",
        "Objective 1",
        "Existing approach 1",
        "Feature 1",
        "Screenshots / Flow",
        "Technical challenges",
        "Enhancements ( if any)",
    ):
        assert placeholder not in text


def test_final_deck_uses_current_source_backed_claims_and_boundaries():
    text = " ".join(_deck_slide_text())
    claims = _machine_claims()

    for current_claim in (
        "Phase 1 + Phase 2",
        *claims.values(),
        "74.41% accuracy",
        "71.49% F1",
        "not directly comparable",
        "no legitimate class",
        "no production-accuracy claim",
        "Human review required",
    ):
        assert current_claim in text

    for stale_claim in (
        "15 automated tests",
        "No OCR in Phase 1",
        "No graph analytics",
        "1.0000 macro-F1",
        "16 test rows",
    ):
        assert stale_claim not in text


def test_final_deck_describes_only_the_supported_interfaces():
    slide_text = " ".join(_deck_slide_text()).lower()
    assert "streamlit" not in slide_text
    assert "api and dashboard" not in slide_text
    assert "next.js" in slide_text
    assert "fastapi" in slide_text

    with zipfile.ZipFile(DECK) as archive:
        package_text = " ".join(
            archive.read(name).decode("utf-8", errors="ignore").lower()
            for name in archive.namelist()
            if name.endswith(".xml")
        )
    assert "streamlit" not in package_text


def test_final_deck_embeds_the_current_architecture_evidence():
    expected = (
        ROOT / "outputs" / "presentation" / "final_system_architecture.png"
    ).read_bytes()

    with zipfile.ZipFile(DECK) as archive:
        slide = archive.read("ppt/slides/slide5.xml").decode("utf-8")
        relationship_id = re.search(
            r'<a:blip r:embed="([^"]+)"', slide
        ).group(1)
        relationships = archive.read(
            "ppt/slides/_rels/slide5.xml.rels"
        ).decode("utf-8")
        target = re.search(
            rf'<Relationship Id="{relationship_id}"[^>]+Target="([^"]+)"',
            relationships,
        ).group(1)
        media_name = posixpath.normpath(posixpath.join("ppt/slides", target))

        assert archive.read(media_name) == expected


def test_final_deck_embeds_the_current_website_demo_evidence():
    expected_paths = (
        ROOT / "outputs" / "screenshots" / "final_text_analysis.png",
        ROOT / "outputs" / "screenshots" / "final_ocr_analysis.png",
        ROOT / "outputs" / "screenshots" / "final_entity_graph.png",
    )

    with zipfile.ZipFile(DECK) as archive:
        slide = archive.read("ppt/slides/slide7.xml").decode("utf-8")
        relationship_ids = re.findall(r'<a:blip r:embed="([^"]+)"', slide)
        relationships = archive.read(
            "ppt/slides/_rels/slide7.xml.rels"
        ).decode("utf-8")

        assert len(relationship_ids) == len(expected_paths)
        for relationship_id, expected_path in zip(
            relationship_ids, expected_paths, strict=True
        ):
            target = re.search(
                rf'<Relationship Id="{relationship_id}"[^>]+Target="([^"]+)"',
                relationships,
            ).group(1)
            media_name = posixpath.normpath(posixpath.join("ppt/slides", target))
            assert archive.read(media_name) == expected_path.read_bytes()


def test_video_runbook_covers_the_recorded_demo_without_a_script_file():
    runbook = RUNBOOK.read_text(encoding="utf-8")

    assert "## Recording sequence" in runbook
    assert "## Failure-safe fallback" in runbook
    assert "outputs/screenshots/final_ocr_analysis.png" in runbook
    assert "outputs/screenshots/final_entity_graph.png" in runbook
    assert "Fake KYC" in runbook


def test_final_report_and_readme_point_to_the_defensible_evidence_package():
    report = FINAL_REPORT.read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    weekly = (ROOT / "docs" / "weekly_progress.md").read_text(encoding="utf-8")
    supervisor = (ROOT / "docs" / "supervisor_interaction.md").read_text(
        encoding="utf-8"
    )
    supervisor_normalized = " ".join(supervisor.split())
    runbook = RUNBOOK.read_text(encoding="utf-8")
    claims = _machine_claims()

    for section in (
        "## Phase 1 Foundation",
        "## Phase 2 Completion",
        "## Research Comparison",
        "## Evaluation Parameters And Rationale",
        "## Threats To Validity",
        "## Reproducibility",
    ):
        assert section in report
    assert "character TF-IDF" in report
    assert "74.41% accuracy and 71.49% F1" in report
    assert "HingRoBERTa complaint classifier [7]" in report
    assert "Neural phishing-URL detector [9]" in report
    assert "Financial-fraud GNNs [10]" in report
    assert "not a shared leaderboard" in report
    assert "docs/presentation/fraudlens-bharat-final-capstone.pptx" in readme
    assert "docs/final_capstone_report.md" in readme
    for document in (report, runbook, weekly):
        assert claims["test_count"] in document
        assert "355 automated tests" not in document
    assert "Phase 2" in weekly
    assert "does not represent supervisor feedback" in weekly
    assert "Phase 2" in supervisor_normalized and "Final review" in supervisor_normalized
    assert "They are not recorded supervisor feedback" in supervisor_normalized
    assert "Pending meeting; no supervisor feedback recorded" in supervisor_normalized
