"""Fixed candidate model families for the academic comparison."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


@dataclass(frozen=True)
class ResearchModel:
    name: str
    representation: str
    fit_required: bool
    calibrated: bool = False


def build_candidate_models(seed: int = 42) -> tuple[ResearchModel, ...]:
    """Return a stable family order from transparent rules to calibrated hybrid."""
    del seed
    return (
        ResearchModel("rule_only", "canonical_runtime_keyword_rules", False),
        ResearchModel("word_tfidf_logistic_regression", "word_ngrams_1_2", True),
        ResearchModel("character_tfidf_logistic_regression", "character_ngrams_3_5", True),
        ResearchModel(
            "word_character_tfidf_logistic_regression",
            "word_ngrams_1_2_plus_character_ngrams_3_5",
            True,
        ),
        ResearchModel(
            "calibrated_word_character_tfidf",
            "word_ngrams_1_2_plus_character_ngrams_3_5",
            True,
            calibrated=True,
        ),
    )


def build_estimator(candidate: ResearchModel, seed: int = 42):
    """Construct a fresh estimator for one declared candidate."""
    if not candidate.fit_required:
        raise ValueError("rule-only candidate has no fitted estimator")
    classifier = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=seed,
    )
    if candidate.name == "word_tfidf_logistic_regression":
        pipeline = Pipeline((("features", _word_vectorizer()), ("classifier", classifier)))
    elif candidate.name == "character_tfidf_logistic_regression":
        pipeline = Pipeline((("features", _character_vectorizer()), ("classifier", classifier)))
    else:
        pipeline = Pipeline((("features", _hybrid_features()), ("classifier", classifier)))
    if candidate.calibrated:
        return CalibratedClassifierCV(estimator=pipeline, method="sigmoid", cv=3)
    return pipeline


def normalize_research_estimator(estimator, decimals: int = 12) -> None:
    """Remove insignificant cross-platform BLAS drift from learned parameters."""
    if decimals < 0:
        raise ValueError("decimals must be non-negative")
    if isinstance(estimator, Pipeline):
        for _, step in estimator.steps:
            normalize_research_estimator(step, decimals)
        return
    if isinstance(estimator, FeatureUnion):
        for _, step in estimator.transformer_list:
            normalize_research_estimator(step, decimals)
        return
    if isinstance(estimator, LogisticRegression):
        estimator.coef_ = np.round(estimator.coef_, decimals)
        estimator.intercept_ = np.round(estimator.intercept_, decimals)
        return
    if isinstance(estimator, CalibratedClassifierCV):
        for calibrated in estimator.calibrated_classifiers_:
            normalize_research_estimator(calibrated.estimator, decimals)
            for calibrator in calibrated.calibrators:
                calibrator.a_ = round(float(calibrator.a_), decimals)
                calibrator.b_ = round(float(calibrator.b_), decimals)


def _word_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        lowercase=False,
        sublinear_tf=True,
        token_pattern=r"(?u)\b\w\w+\b",
    )


def _character_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        lowercase=False,
        sublinear_tf=True,
    )


def _hybrid_features() -> FeatureUnion:
    return FeatureUnion((("word", _word_vectorizer()), ("character", _character_vectorizer())))
