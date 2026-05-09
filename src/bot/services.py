from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.coaching import compare_telemetry
from src.data_loader import get_race_info, load_results, load_weather
from src.lap_analysis import (
    get_all_drivers_consistency,
    get_driver_lap_times,
    get_fastest_laps,
    get_lap_time_evolution,
)
from src.race_analysis import get_final_standings, get_position_change_summary, get_team_standings
from src.telemetry_analysis import get_gear_time_distribution, get_speed_profile, get_throttle_brake_analysis
from src.tyre_analysis import get_compound_comparison, get_tyre_degradation, get_tyre_strategy
from src.weather_analysis import get_weather_summary, get_weather_timeline

from .types import (
    DEFAULT_BOT_OUTPUT_DIR,
    DEFAULT_COMPARE_BENCHMARK_CSV,
    DEFAULT_COMPARE_USER_CSV,
    BotResponse,
)


class BotService:
    """Service layer that wraps the existing analysis modules."""

    def __init__(
        self,
        driver: str = "VER",
        compare_user_csv: str | Path = DEFAULT_COMPARE_USER_CSV,
        compare_benchmark_csv: str | Path = DEFAULT_COMPARE_BENCHMARK_CSV,
        output_dir: str | Path = DEFAULT_BOT_OUTPUT_DIR,
    ) -> None:
        self.driver = driver
        self.compare_user_csv = Path(compare_user_csv)
        self.compare_benchmark_csv = Path(compare_benchmark_csv)
        self.output_dir = Path(output_dir)

    def get_standings_response(self) -> BotResponse:
        race_info = get_race_info()
        final_standings = get_final_standings()
        position_changes = get_position_change_summary()
        team_standings = get_team_standings()

        summary = [
            f"{race_info['event']} @ {race_info['circuit']}",
            f"冠軍：{race_info['winner']} ({race_info['winner_team']})",
            f"總圈數：{race_info['total_laps']} 圈；參賽車手：{race_info['drivers']} 位；完賽：{race_info['finishers']} 位",
        ]

        metrics = {
            "winner": race_info["winner"],
            "winner_team": race_info["winner_team"],
            "total_laps": race_info["total_laps"],
            "drivers": race_info["drivers"],
            "finishers": race_info["finishers"],
        }

        tables = {
            "final_standings": final_standings,
            "position_changes": position_changes,
            "team_standings": team_standings,
        }

        return BotResponse(
            command="standings",
            title="最終排名 / 車隊積分",
            summary=summary,
            metrics=metrics,
            tables=tables,
            details={"race_info": race_info},
        )

    def get_strategy_response(self) -> BotResponse:
        strategy = get_tyre_strategy()
        degradation = get_tyre_degradation()
        compound_comparison = get_compound_comparison()

        summary = [
            f"策略車手數：{len(strategy)}",
            f"最常見策略：{strategy['strategy'].mode().iloc[0] if len(strategy) else '-'}",
            "輪胎衰退表聚焦於可用樣本數較足夠的 stint。",
        ]

        metrics = {
            "drivers": len(strategy),
            "stints_with_degradation": len(degradation),
            "compounds": sorted(compound_comparison["Compound"].dropna().astype(str).unique().tolist()) if len(compound_comparison) else [],
        }

        tables = {
            "tyre_strategy": strategy,
            "tyre_degradation": degradation.head(12) if len(degradation) else degradation,
            "compound_comparison": compound_comparison,
        }

        return BotResponse(
            command="strategy",
            title="輪胎策略與衰退分析",
            summary=summary,
            metrics=metrics,
            tables=tables,
            details={
                "top_strategy": strategy.iloc[0].to_dict() if len(strategy) else {},
            },
        )

    def get_compare_response(
        self,
        user_csv: str | Path | None = None,
        benchmark_csv: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> BotResponse:
        user_csv = Path(user_csv) if user_csv else self.compare_user_csv
        benchmark_csv = Path(benchmark_csv) if benchmark_csv else self.compare_benchmark_csv
        output_dir = Path(output_dir) if output_dir else self.output_dir / "compare"

        comparison = compare_telemetry(user_csv=user_csv, benchmark_csv=benchmark_csv, output_dir=output_dir)

        events = pd.DataFrame(comparison.get("events", []))
        segments = pd.DataFrame(comparison.get("segment_summary", []))
        feedback = comparison.get("feedback", [])

        summary = [
            f"比對區間：{comparison['overlap_distance']['start_m']:.1f}m ~ {comparison['overlap_distance']['end_m']:.1f}m",
            f"平均速度差：{comparison['speed_delta']['mean_kph']:+.2f} km/h",
            f"配對煞車區段：{comparison['event_count']['paired_zones']} 組",
        ]

        metrics = {
            "mean_speed_delta_kph": comparison["speed_delta"]["mean_kph"],
            "median_speed_delta_kph": comparison["speed_delta"]["median_kph"],
            "paired_zones": comparison["event_count"]["paired_zones"],
            "benchmark_brake_zones": comparison["event_count"]["benchmark_brake_zones"],
            "user_brake_zones": comparison["event_count"]["user_brake_zones"],
        }

        tables = {
            "events": events,
            "segments": segments,
        }

        return BotResponse(
            command="compare",
            title="遙測對比與教練回饋",
            summary=summary,
            metrics=metrics,
            tables=tables,
            details={
                "feedback": feedback,
                "output_files": comparison.get("output_files", {}),
                "user_csv": str(user_csv.resolve()),
                "benchmark_csv": str(benchmark_csv.resolve()),
            },
            artifacts={k: str(v) for k, v in comparison.get("output_files", {}).items()},
        )

    def get_weather_response(self) -> BotResponse:
        weather_summary = get_weather_summary()
        weather_timeline = get_weather_timeline()

        summary = [
            f"降雨：{'有' if weather_summary['rainfall'] else '無'}",
            f"氣溫：{weather_summary['air_temp']['min']:.1f} ~ {weather_summary['air_temp']['max']:.1f} °C",
            f"賽道溫度：{weather_summary['track_temp']['min']:.1f} ~ {weather_summary['track_temp']['max']:.1f} °C",
        ]

        metrics = {
            "rainfall": weather_summary["rainfall"],
            "records_count": weather_summary["records_count"],
            "wind_speed_avg": weather_summary["wind_speed"]["avg"],
        }

        weather_frame = pd.DataFrame(
            [
                {
                    "metric": "air_temp_min",
                    "value": weather_summary["air_temp"]["min"],
                },
                {
                    "metric": "air_temp_max",
                    "value": weather_summary["air_temp"]["max"],
                },
                {
                    "metric": "track_temp_min",
                    "value": weather_summary["track_temp"]["min"],
                },
                {
                    "metric": "track_temp_max",
                    "value": weather_summary["track_temp"]["max"],
                },
                {
                    "metric": "humidity_avg",
                    "value": weather_summary["humidity"]["avg"],
                },
            ]
        )

        tables = {
            "weather_summary": weather_frame,
            "weather_timeline": weather_timeline.head(12),
        }

        return BotResponse(
            command="weather",
            title="天氣摘要與時間序列",
            summary=summary,
            metrics=metrics,
            tables=tables,
            details={"weather_summary": weather_summary},
        )

    def get_telemetry_response(self, driver: str | None = None) -> BotResponse:
        driver = driver or self.driver
        analysis = get_throttle_brake_analysis(driver)
        speed_profile = get_speed_profile(driver)
        gear_distribution = pd.DataFrame(
            [
                {"gear": gear, "count": values["count"], "pct": values["pct"]}
                for gear, values in get_gear_time_distribution(driver)["gear_distribution"].items()
            ]
        )

        summary = [
            f"車手：{driver}",
            f"平均速度：{analysis['avg_speed']:.1f} km/h；最高速度：{analysis['max_speed']:.1f} km/h",
            f"全油門：{analysis['full_throttle_pct']:.1f}%；煞車：{analysis['braking_pct']:.1f}%；滑行：{analysis['coasting_pct']:.1f}%",
        ]

        metrics = {
            "driver": driver,
            "avg_speed": analysis["avg_speed"],
            "max_speed": analysis["max_speed"],
            "full_throttle_pct": analysis["full_throttle_pct"],
            "braking_pct": analysis["braking_pct"],
            "coasting_pct": analysis["coasting_pct"],
            "drs_active_pct": analysis["drs_active_pct"],
            "brake_points": analysis["brake_points"],
        }

        tables = {
            "gear_distribution": gear_distribution,
            "speed_profile": speed_profile.head(15),
        }

        return BotResponse(
            command="telemetry",
            title=f"遙測摘要：{driver}",
            summary=summary,
            metrics=metrics,
            tables=tables,
            details={"analysis": analysis},
        )

    def get_laps_response(self, driver: str | None = None) -> BotResponse:
        driver = driver or self.driver
        fastest_laps = get_fastest_laps()
        driver_laps = get_driver_lap_times(driver)
        consistency = get_all_drivers_consistency()
        evolution = get_lap_time_evolution([driver])

        driver_consistency = consistency[consistency["Driver"] == driver].iloc[0].to_dict() if len(consistency[consistency["Driver"] == driver]) else {}

        summary = [
            f"車手：{driver}",
            f"最快圈速榜取前 10 名，並顯示 {driver} 的完整圈速序列。",
            f"一致性排名以變異係數 CV 排序。",
        ]

        metrics = {
            "driver": driver,
            "driver_laps": len(driver_laps),
            "fastest_laps_count": len(fastest_laps),
            "consistency_cv": driver_consistency.get("cv"),
        }

        tables = {
            "fastest_laps": fastest_laps.head(10),
            "driver_laps": driver_laps,
            "consistency": consistency.head(10),
            "lap_evolution": evolution,
        }

        return BotResponse(
            command="laps",
            title=f"圈速分析：{driver}",
            summary=summary,
            metrics=metrics,
            tables=tables,
            details={"driver_consistency": driver_consistency},
        )
