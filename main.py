from __future__ import annotations

import argparse
from pathlib import Path

from src.reports import generate_race_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Monza 2024 race report.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "outputs" / "reports",
        help="Directory to write the Markdown and HTML reports.",
    )
    parser.add_argument(
        "--driver",
        type=str,
        default="VER",
        help="Driver code to use for telemetry summary (default: VER).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = generate_race_report(output_dir=args.output_dir, driver=args.driver)
    print(f"Generated Markdown report: {paths['markdown']}")
    print(f"Generated HTML report: {paths['html']}")


if __name__ == "__main__":
    main()
