"""Artifact generation for the Monza 2024 prediction baseline."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .baseline import build_prediction_table

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "prediction"
DEFAULT_CSV_PATH = DEFAULT_OUTPUT_DIR / "monza_2024_predictions.csv"
DEFAULT_MD_PATH = DEFAULT_OUTPUT_DIR / "monza_2024_predictions.md"


def _format_table(df: pd.DataFrame, columns: list[str]) -> str:
    if len(df) == 0:
        return "_No data available_"

    display_df = df.loc[:, [c for c in columns if c in df.columns]].copy()
    for col in display_df.columns:
        if pd.api.types.is_float_dtype(display_df[col]):
            display_df[col] = display_df[col].map(lambda x: "-" if pd.isna(x) else f"{x:.3f}")
        else:
            display_df[col] = display_df[col].map(lambda x: "-" if pd.isna(x) else str(x))

    headers = [str(col) for col in display_df.columns]
    rows = display_df.astype(str).values.tolist()
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))

    def fmt(values: list[str]) -> str:
        return "| " + " | ".join(values[idx].ljust(widths[idx]) for idx in range(len(values))) + " |"

    header = fmt(headers)
    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    body = "\n".join(fmt(row) for row in rows)
    return "\n".join([header, separator, body])


def _render_markdown(predictions: pd.DataFrame) -> str:
    top_cols = ["rank", "driver", "full_name", "team_name", "predicted_result_class", "predicted_gain_band", "predicted_strategy"]
    top = predictions.copy()
    top.insert(0, "rank", range(1, len(top) + 1))

    summary = {
        "top3": int((top["predicted_result_class"] == "Top 3").sum()),
        "top10": int((top["predicted_result_class"] == "Top 10").sum()),
        "dnf": int((top["predicted_result_class"] == "DNF").sum()),
        "one_stop": int((top["predicted_strategy"] == "One-stop").sum()),
        "two_stop": int((top["predicted_strategy"] == "Two-stop").sum()),
    }

    lines = [
        "# Monza 2024 baseline predictions",
        "",
        "This artifact contains an explainable rule-based baseline for three outputs per driver:",
        "Top 3 / Top 10 / DNF class, start-finish gain band, and one-stop vs two-stop strategy.",
        "",
        "## Summary",
        f"- Drivers: {len(top)}",
        f"- Predicted Top 3: {summary['top3']}",
        f"- Predicted Top 10: {summary['top10']}",
        f"- Predicted DNF bucket: {summary['dnf']}",
        f"- Predicted One-stop: {summary['one_stop']}",
        f"- Predicted Two-stop: {summary['two_stop']}",
        "",
        "## Driver predictions",
        _format_table(top, top_cols),
        "",
        "## Notes",
        "- Result class is a transparent ranking bucket built from grid, pace, consistency, degradation and team proxy scores.",
        "- Gain band is derived from predicted finish rank minus grid position.",
        "- Strategy is based on stint count, longest stint length, hard-tyre share and tyre degradation slope.",
        "- DNF is used as the coarse lower bucket for drivers outside the top 10 in this baseline.",
    ]
    return "\n".join(lines)


def generate_prediction_artifacts(output_dir: str | Path | None = None, save: bool = True, accurate_only: bool = True) -> dict[str, Path]:
    predictions = build_prediction_table(accurate_only=accurate_only)

    output_dir = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / DEFAULT_CSV_PATH.name
    md_path = output_dir / DEFAULT_MD_PATH.name

    if save:
        predictions.to_csv(csv_path, index=False)
        md_path.write_text(_render_markdown(predictions), encoding="utf-8")

    return {"csv": csv_path, "markdown": md_path}


def load_prediction_table(path: str | Path | None = None) -> pd.DataFrame:
    file_path = Path(path) if path is not None else DEFAULT_CSV_PATH
    return pd.read_csv(file_path)
