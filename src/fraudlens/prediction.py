"""Stable prediction boundary shared by trained and fallback predictors."""

from dataclasses import dataclass
from typing import Dict, Protocol, runtime_checkable


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float
    source: str
    model_version: str
    abstained: bool


@runtime_checkable
class Predictor(Protocol):
    def predict(self, text: str) -> Prediction:
        """Return one calibrated prediction, or an explicit abstention."""


class PredictorRegistry:
    """Small injection-friendly registry for selectable predictor backends."""

    def __init__(self, predictors: Dict[str, Predictor]):
        self._predictors = dict(predictors)

    def get(self, name: str) -> Predictor:
        try:
            return self._predictors[name]
        except KeyError as error:
            raise ValueError("Unsupported predictor backend: {}".format(name)) from error
