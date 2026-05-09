"""Monza 2024 prediction baseline package."""
from __future__ import annotations

from importlib import import_module

__all__ = [
    "build_prediction_table",
    "generate_prediction_artifacts",
    "get_driver_prediction_features",
    "load_prediction_table",
    "predict_driver_baseline",
]


def __getattr__(name):
    if name in {"build_prediction_table", "predict_driver_baseline"}:
        module = import_module("src.prediction.baseline")
        return getattr(module, name)
    if name in {"generate_prediction_artifacts", "load_prediction_table"}:
        module = import_module("src.prediction.generator")
        return getattr(module, name)
    if name in {"get_driver_prediction_features"}:
        module = import_module("src.prediction.features")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
