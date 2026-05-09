"""
VER 遙測教練基線

功能：
- 將使用者遙測 CSV 與 benchmark telemetry_VER.csv 依 Distance 對齊
- 產出可執行的教練回饋：早/晚煞車、油門回補時機、速度差摘要
- 匯出 JSON 與簡短文字摘要到 outputs/coaching/

不依賴任何外部模擬器 SDK。
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "raw"
DEFAULT_BENCHMARK = RAW_DIR / "telemetry_VER.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "coaching"

REQUIRED_COLUMNS = ["Distance", "Speed", "Throttle", "Brake"]
OPTIONAL_NUMERIC_COLUMNS = [
    "RelativeDistance",
    "RPM",
    "nGear",
    "DRS",
    "DistanceToDriverAhead",
    "X",
    "Y",
    "Z",
]


@dataclass
class EventPair:
    index: int
    ref_brake_start: float
    user_brake_start: float
    brake_delta_m: float
    ref_throttle_pickup: float
    user_throttle_pickup: float
    throttle_delta_m: float


def _to_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(bool)
    text = series.astype(str).str.strip().str.lower()
    return text.isin({"true", "1", "t", "yes", "y"})


def load_telemetry_csv(path: str | Path) -> pd.DataFrame:
    """載入並清理遙測資料。"""
    path = Path(path)
    df = pd.read_csv(path)

    for col in ["Distance", "Speed", "Throttle", *OPTIONAL_NUMERIC_COLUMNS]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Brake" in df.columns:
        df["Brake"] = _to_bool_series(df["Brake"])
    else:
        df["Brake"] = False

    if "Distance" not in df.columns:
        raise ValueError(f"缺少 Distance 欄位：{path}")

    df = df.dropna(subset=["Distance"]).copy()
    df = df.sort_values("Distance").reset_index(drop=True)

    # 合併重複 Distance，以避免插值時出現問題
    agg: Dict[str, str] = {"Brake": "max"}
    for col in df.columns:
        if col == "Distance":
            continue
        if col == "Brake":
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            agg[col] = "mean"
        else:
            agg[col] = "last"
    df = df.groupby("Distance", as_index=False).agg(agg)
    return df


def _interp_series(df: pd.DataFrame, grid: np.ndarray, col: str) -> np.ndarray:
    if col not in df.columns:
        return np.full_like(grid, np.nan, dtype=float)

    x = df["Distance"].to_numpy(dtype=float)
    y = df[col].to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    if valid.sum() < 2:
        return np.full_like(grid, np.nan, dtype=float)
    x = x[valid]
    y = y[valid]
    order = np.argsort(x)
    x = x[order]
    y = y[order]
    unique_x, unique_idx = np.unique(x, return_index=True)
    y = y[unique_idx]
    if len(unique_x) < 2:
        return np.full_like(grid, np.nan, dtype=float)
    return np.interp(grid, unique_x, y)


def align_by_distance(ref_df: pd.DataFrame, user_df: pd.DataFrame, n_points: int = 700) -> pd.DataFrame:
    """依共同距離範圍對齊兩份遙測。"""
    start = max(float(ref_df["Distance"].min()), float(user_df["Distance"].min()))
    end = min(float(ref_df["Distance"].max()), float(user_df["Distance"].max()))
    if not np.isfinite(start) or not np.isfinite(end) or end <= start:
        raise ValueError("兩份遙測資料沒有可用的共同 Distance 區間")

    grid = np.linspace(start, end, n_points)
    out = pd.DataFrame({"Distance": grid})

    for col in ["Speed", "Throttle", "RPM", "nGear", "DRS", "DistanceToDriverAhead", "RelativeDistance", "X", "Y", "Z"]:
        out[f"{col}_ref"] = _interp_series(ref_df, grid, col)
        out[f"{col}_user"] = _interp_series(user_df, grid, col)

    brake_ref = _interp_series(ref_df, grid, "Brake")
    brake_user = _interp_series(user_df, grid, "Brake")
    out["Brake_ref"] = brake_ref >= 0.5
    out["Brake_user"] = brake_user >= 0.5
    out["Speed_delta"] = out["Speed_user"] - out["Speed_ref"]
    out["Throttle_delta"] = out["Throttle_user"] - out["Throttle_ref"]
    return out


def _find_segments(mask: np.ndarray) -> List[Tuple[int, int]]:
    mask = mask.astype(bool)
    starts = np.where((mask[1:] & ~mask[:-1]))[0] + 1
    ends = np.where((~mask[1:] & mask[:-1]))[0] + 1
    if mask.size and mask[0]:
        starts = np.r_[0, starts]
    if mask.size and mask[-1]:
        ends = np.r_[ends, mask.size]
    segments: List[Tuple[int, int]] = []
    for s, e in zip(starts, ends):
        if e > s:
            segments.append((int(s), int(e)))
    return segments


def _first_crossing_distance(dist: np.ndarray, signal: np.ndarray, start_idx: int, threshold: float, direction: str) -> Optional[float]:
    if start_idx >= len(signal):
        return None
    segment = signal[start_idx:]
    if direction == "up":
        idx = np.where(segment >= threshold)[0]
    else:
        idx = np.where(segment <= threshold)[0]
    if len(idx) == 0:
        return None
    return float(dist[start_idx + int(idx[0])])


def _pair_segments_monotonic(
    ref_segments: List[Tuple[int, int]],
    user_segments: List[Tuple[int, int]],
    dist: np.ndarray,
    skip_penalty: float = 200.0,
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """用動態規劃做單調配對，避免數量不一致時錯配。"""
    n = len(ref_segments)
    m = len(user_segments)
    if n == 0 or m == 0:
        return []

    ref_starts = [float(dist[s]) for s, _ in ref_segments]
    user_starts = [float(dist[s]) for s, _ in user_segments]

    dp = np.zeros((n + 1, m + 1), dtype=float)
    action = np.zeros((n + 1, m + 1), dtype=np.int8)

    for i in range(n - 1, -1, -1):
        dp[i, m] = (n - i) * skip_penalty
        action[i, m] = 1
    for j in range(m - 1, -1, -1):
        dp[n, j] = (m - j) * skip_penalty
        action[n, j] = 2

    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            match_cost = abs(ref_starts[i] - user_starts[j]) + dp[i + 1, j + 1]
            skip_ref_cost = skip_penalty + dp[i + 1, j]
            skip_user_cost = skip_penalty + dp[i, j + 1]
            best = min(match_cost, skip_ref_cost, skip_user_cost)
            dp[i, j] = best
            if best == match_cost:
                action[i, j] = 0
            elif best == skip_ref_cost:
                action[i, j] = 1
            else:
                action[i, j] = 2

    pairs: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
    i = j = 0
    while i < n and j < m:
        act = int(action[i, j])
        if act == 0:
            pairs.append((ref_segments[i], user_segments[j]))
            i += 1
            j += 1
        elif act == 1:
            i += 1
        else:
            j += 1
    return pairs


def detect_braking_and_throttle_events(aligned: pd.DataFrame, brake_threshold: float = 0.5, throttle_threshold: float = 25.0) -> List[EventPair]:
    """依煞車區段配對煞車起點與油門回補點。"""
    dist = aligned["Distance"].to_numpy(dtype=float)
    brake_ref = aligned["Brake_ref"].to_numpy(dtype=bool)
    brake_user = aligned["Brake_user"].to_numpy(dtype=bool)
    thr_ref = aligned["Throttle_ref"].to_numpy(dtype=float)
    thr_user = aligned["Throttle_user"].to_numpy(dtype=float)

    ref_segments = _find_segments(brake_ref)
    user_segments = _find_segments(brake_user)
    paired_segments = _pair_segments_monotonic(ref_segments, user_segments, dist)
    pairs: List[EventPair] = []

    for i, (ref_seg, user_seg) in enumerate(paired_segments):
        rs, re = ref_seg
        us, ue = user_seg
        ref_brake_start = float(dist[rs])
        user_brake_start = float(dist[us])

        ref_throttle_pickup = _first_crossing_distance(dist, thr_ref, re, throttle_threshold, "up")
        user_throttle_pickup = _first_crossing_distance(dist, thr_user, ue, throttle_threshold, "up")

        if ref_throttle_pickup is None:
            ref_throttle_pickup = float(dist[min(re, len(dist) - 1)])
        if user_throttle_pickup is None:
            user_throttle_pickup = float(dist[min(ue, len(dist) - 1)])

        pairs.append(
            EventPair(
                index=i + 1,
                ref_brake_start=ref_brake_start,
                user_brake_start=user_brake_start,
                brake_delta_m=user_brake_start - ref_brake_start,
                ref_throttle_pickup=ref_throttle_pickup,
                user_throttle_pickup=user_throttle_pickup,
                throttle_delta_m=user_throttle_pickup - ref_throttle_pickup,
            )
        )

    return pairs


def _verdict(delta_m: float, threshold_m: float, early_label: str, late_label: str) -> str:
    if delta_m > threshold_m:
        return late_label
    if delta_m < -threshold_m:
        return early_label
    return "接近 benchmark"


def _segment_summary(aligned: pd.DataFrame, n_segments: int = 20) -> List[dict]:
    bins = np.linspace(float(aligned["Distance"].min()), float(aligned["Distance"].max()), n_segments + 1)
    seg_ids = pd.cut(aligned["Distance"], bins=bins, labels=False, include_lowest=True)
    rows: List[dict] = []
    for seg_idx in range(n_segments):
        chunk = aligned[seg_ids == seg_idx]
        if chunk.empty:
            continue
        rows.append(
            {
                "segment": f"S{seg_idx + 1:02d}",
                "distance_start": float(bins[seg_idx]),
                "distance_end": float(bins[seg_idx + 1]),
                "avg_speed_ref": float(chunk["Speed_ref"].mean()),
                "avg_speed_user": float(chunk["Speed_user"].mean()),
                "speed_delta": float(chunk["Speed_delta"].mean()),
                "avg_throttle_ref": float(chunk["Throttle_ref"].mean()),
                "avg_throttle_user": float(chunk["Throttle_user"].mean()),
                "avg_brake_ref": float(chunk["Brake_ref"].mean()),
                "avg_brake_user": float(chunk["Brake_user"].mean()),
            }
        )
    return rows


def _build_feedback(event_pairs: List[EventPair], aligned: pd.DataFrame) -> List[str]:
    messages: List[str] = []
    if not event_pairs:
        messages.append("未偵測到足夠的煞車區段，無法生成煞車/油門教練建議。")
        return messages

    late_brakes = sum(1 for p in event_pairs if p.brake_delta_m > 3.0)
    early_brakes = sum(1 for p in event_pairs if p.brake_delta_m < -3.0)
    late_throttle = sum(1 for p in event_pairs if p.throttle_delta_m > 3.0)
    early_throttle = sum(1 for p in event_pairs if p.throttle_delta_m < -3.0)

    if late_brakes:
        messages.append(f"有 {late_brakes} 個煞車點偏晚；可嘗試提早約 3–5m 開始制動，讓入彎速度更穩。")
    if early_brakes:
        messages.append(f"有 {early_brakes} 個煞車點偏早；若輪胎與抓地允許，可延後些許煞車以提升單圈速度。")
    if late_throttle:
        messages.append(f"有 {late_throttle} 個出彎油門回補偏晚；可在車身更穩後提早漸進補油。")
    if early_throttle:
        messages.append(f"有 {early_throttle} 個出彎油門回補偏早；若出現打滑，建議保守維持，否則可嘗試更早開油。")

    mean_delta = float(aligned["Speed_delta"].mean())
    min_delta = float(aligned["Speed_delta"].min())
    max_delta = float(aligned["Speed_delta"].max())
    if mean_delta < -0.5:
        messages.append(f"整體平均速度比 benchmark 慢 {abs(mean_delta):.2f} km/h，主要損失可從煞車點與油門銜接處下手。")
    elif mean_delta > 0.5:
        messages.append(f"整體平均速度比 benchmark 快 {mean_delta:.2f} km/h，基線表現不錯。")
    else:
        messages.append("整體平均速度與 benchmark 接近，主要差異集中在特定煞車區段。")

    messages.append(f"最大速度落後約 {abs(min_delta):.2f} km/h；最大領先約 {max_delta:.2f} km/h。")
    return messages


def compare_telemetry(user_csv: str | Path, benchmark_csv: str | Path = DEFAULT_BENCHMARK, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> dict:
    """比較使用者遙測與 benchmark，並寫出 JSON / TXT。"""
    user_df = load_telemetry_csv(user_csv)
    ref_df = load_telemetry_csv(benchmark_csv)
    aligned = align_by_distance(ref_df, user_df)

    event_pairs = detect_braking_and_throttle_events(aligned)
    speed_delta = aligned["Speed_delta"].to_numpy(dtype=float)

    summary = {
        "benchmark_csv": str(Path(benchmark_csv).resolve()),
        "user_csv": str(Path(user_csv).resolve()),
        "overlap_distance": {
            "start_m": float(aligned["Distance"].min()),
            "end_m": float(aligned["Distance"].max()),
            "samples": int(len(aligned)),
        },
        "speed_delta": {
            "mean_kph": float(np.nanmean(speed_delta)),
            "median_kph": float(np.nanmedian(speed_delta)),
            "min_kph": float(np.nanmin(speed_delta)),
            "max_kph": float(np.nanmax(speed_delta)),
            "p10_kph": float(np.nanpercentile(speed_delta, 10)),
            "p90_kph": float(np.nanpercentile(speed_delta, 90)),
        },
        "event_count": {
            "benchmark_brake_zones": int(len(_find_segments(aligned["Brake_ref"].to_numpy(dtype=bool)))),
            "user_brake_zones": int(len(_find_segments(aligned["Brake_user"].to_numpy(dtype=bool)))),
            "paired_zones": int(len(event_pairs)),
        },
        "events": [],
        "segment_summary": _segment_summary(aligned),
    }

    for pair in event_pairs:
        summary["events"].append(
            {
                "zone_index": pair.index,
                "ref_brake_start_m": pair.ref_brake_start,
                "user_brake_start_m": pair.user_brake_start,
                "brake_delta_m": pair.brake_delta_m,
                "brake_verdict": _verdict(pair.brake_delta_m, 3.0, "偏早煞車", "偏晚煞車"),
                "ref_throttle_pickup_m": pair.ref_throttle_pickup,
                "user_throttle_pickup_m": pair.user_throttle_pickup,
                "throttle_delta_m": pair.throttle_delta_m,
                "throttle_verdict": _verdict(pair.throttle_delta_m, 3.0, "油門回補偏早", "油門回補偏晚"),
            }
        )

    summary["feedback"] = _build_feedback(event_pairs, aligned)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "coaching_report.json"
    txt_path = output_dir / "coaching_summary.txt"

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["VER 遙測教練摘要"]
    lines.append(
        f"- 比對區間：{summary['overlap_distance']['start_m']:.1f}m ~ {summary['overlap_distance']['end_m']:.1f}m，共 {summary['overlap_distance']['samples']} 點"
    )
    lines.append(
        f"- 平均速度差：{summary['speed_delta']['mean_kph']:+.2f} km/h；中位數：{summary['speed_delta']['median_kph']:+.2f} km/h"
    )
    lines.append(
        f"- 速度差範圍：{summary['speed_delta']['min_kph']:+.2f} ~ {summary['speed_delta']['max_kph']:+.2f} km/h"
    )
    for msg in summary["feedback"][:6]:
        lines.append(f"- {msg}")
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary["output_files"] = {"json": str(json_path), "text": str(txt_path)}
    return summary


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VER telemetry coaching baseline")
    parser.add_argument("user_csv", help="使用者遙測 CSV 路徑")
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK), help="benchmark 遙測 CSV")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="輸出目錄")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    result = compare_telemetry(args.user_csv, args.benchmark, args.output_dir)
    print(json.dumps({
        "json": result["output_files"]["json"],
        "text": result["output_files"]["text"],
        "mean_speed_delta": result["speed_delta"]["mean_kph"],
        "paired_zones": result["event_count"]["paired_zones"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
