from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class BotResponse:
    """Standardized payload returned by bot command handlers."""

    command: str
    title: str
    summary: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CommandSpec:
    name: str
    description: str
    handler_name: str


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "bot"
DEFAULT_COMPARE_USER_CSV = PROJECT_ROOT / "outputs" / "coaching" / "synthetic_user.csv"
DEFAULT_COMPARE_BENCHMARK_CSV = PROJECT_ROOT / "raw" / "telemetry_VER.csv"


COMMAND_SPECS: list[CommandSpec] = [
    CommandSpec("standings", "最終排名與車隊積分", "get_standings_response"),
    CommandSpec("strategy", "輪胎策略與衰退分析", "get_strategy_response"),
    CommandSpec("compare", "遙測對比與教練回饋", "get_compare_response"),
    CommandSpec("weather", "天氣摘要與時間序列", "get_weather_response"),
    CommandSpec("telemetry", "單一車手遙測摘要", "get_telemetry_response"),
    CommandSpec("laps", "圈速、最快圈與一致性", "get_laps_response"),
]
