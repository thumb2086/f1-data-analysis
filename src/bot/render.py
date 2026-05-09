from __future__ import annotations

import json
from dataclasses import is_dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .types import BotResponse


def _format_scalar(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    if isinstance(value, (np.floating, float)):
        if pd.isna(value):
            return "-"
        return f"{float(value):.3f}".rstrip("0").rstrip(".")
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.Timedelta):
        return str(value)
    return str(value)


def dataframe_to_markdown(df: pd.DataFrame | None, max_rows: int | None = None) -> str:
    if df is None or len(df) == 0:
        return "_No data available_"

    display_df = df.copy()
    if max_rows is not None:
        display_df = display_df.head(max_rows)

    headers = [str(col) for col in display_df.columns]
    rows = [[_format_scalar(value) for value in row] for row in display_df.itertuples(index=False, name=None)]
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def fmt_row(values: list[str]) -> str:
        return "| " + " | ".join(values[idx].ljust(widths[idx]) for idx in range(len(values))) + " |"

    header = fmt_row(headers)
    separator = "| " + " | ".join("-" * widths[idx] for idx in range(len(headers))) + " |"
    body = "\n".join(fmt_row(row) for row in rows)
    return "\n".join([header, separator, body])


def dataframe_to_text(df: pd.DataFrame | None, max_rows: int | None = None) -> str:
    if df is None or len(df) == 0:
        return "No data available"
    display_df = df.copy()
    if max_rows is not None:
        display_df = display_df.head(max_rows)
    return display_df.to_string(index=False)


def _render_mapping(mapping: dict[str, Any], indent: int = 0) -> list[str]:
    lines: list[str] = []
    pad = "  " * indent
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{pad}- {key}:")
            lines.extend(_render_mapping(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{pad}- {key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.extend(_render_mapping(item, indent + 1))
                else:
                    lines.append(f"{pad}  - {_format_scalar(item)}")
        else:
            lines.append(f"{pad}- {key}: {_format_scalar(value)}")
    return lines


def render_markdown(response: BotResponse) -> str:
    lines = [f"# {response.title}", ""]
    if response.summary:
        lines.append("## 摘要")
        lines.extend(f"- {line}" for line in response.summary)
        lines.append("")
    if response.metrics:
        lines.append("## 指標")
        lines.extend(_render_mapping(response.metrics))
        lines.append("")
    for name, df in response.tables.items():
        lines.append(f"## {name.replace('_', ' ').title()}")
        lines.append("")
        lines.append(dataframe_to_markdown(df))
        lines.append("")
    if response.details:
        lines.append("## 詳細資料")
        lines.extend(_render_mapping(response.details))
        lines.append("")
    if response.artifacts:
        lines.append("## 輸出檔案")
        lines.extend(_render_mapping(response.artifacts))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_text(response: BotResponse) -> str:
    lines = [response.title, "=" * len(response.title), ""]
    if response.summary:
        lines.append("摘要:")
        lines.extend(f"- {line}" for line in response.summary)
        lines.append("")
    if response.metrics:
        lines.append("指標:")
        lines.extend(_render_mapping(response.metrics))
        lines.append("")
    for name, df in response.tables.items():
        lines.append(name.replace("_", " ").title() + ":")
        lines.append(dataframe_to_text(df))
        lines.append("")
    if response.details:
        lines.append("詳細資料:")
        lines.extend(_render_mapping(response.details))
        lines.append("")
    if response.artifacts:
        lines.append("輸出檔案:")
        lines.extend(_render_mapping(response.artifacts))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, BotResponse):
        return {
            "command": value.command,
            "title": value.title,
            "summary": list(value.summary),
            "metrics": to_jsonable(value.metrics),
            "tables": {name: to_jsonable(df) for name, df in value.tables.items()},
            "details": to_jsonable(value.details),
            "artifacts": to_jsonable(value.artifacts),
        }
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.DataFrame):
        return {
            "columns": [str(col) for col in value.columns],
            "rows": [{str(col): to_jsonable(row[col]) for col in value.columns} for _, row in value.iterrows()],
        }
    if isinstance(value, pd.Series):
        return {str(k): to_jsonable(v) for k, v in value.to_dict().items()}
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.Timedelta):
        return str(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (np.ndarray,)):
        return [to_jsonable(item) for item in value.tolist()]
    return value


def response_to_json(response: BotResponse) -> str:
    return json.dumps(to_jsonable(response), ensure_ascii=False, indent=2)
