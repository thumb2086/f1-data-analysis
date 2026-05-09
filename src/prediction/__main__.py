"""CLI entry point for the Monza 2024 prediction baseline."""
from __future__ import annotations

import argparse
from pathlib import Path

from .generator import generate_prediction_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Monza 2024 prediction baseline artifacts.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where prediction artifacts will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = generate_prediction_artifacts(output_dir=args.output_dir)
    print(f"Generated CSV: {paths['csv']}")
    print(f"Generated Markdown: {paths['markdown']}")


if __name__ == "__main__":
    main()
