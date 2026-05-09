from __future__ import annotations

import argparse
from pathlib import Path

from .commands import BotCommandRunner
from .services import BotService
from .types import DEFAULT_BOT_OUTPUT_DIR, DEFAULT_COMPARE_BENCHMARK_CSV, DEFAULT_COMPARE_USER_CSV


DEMO_COMMANDS = ["standings", "strategy", "compare", "weather", "telemetry", "laps"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CLI demo outputs for the F1 bot scaffold.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_BOT_OUTPUT_DIR, help="Directory for demo artifacts.")
    parser.add_argument("--driver", type=str, default="VER", help="Driver code for telemetry/laps commands.")
    parser.add_argument("--user-csv", type=Path, default=DEFAULT_COMPARE_USER_CSV, help="User telemetry CSV for compare.")
    parser.add_argument("--benchmark-csv", type=Path, default=DEFAULT_COMPARE_BENCHMARK_CSV, help="Benchmark telemetry CSV for compare.")
    parser.add_argument(
        "--commands",
        nargs="*",
        default=DEMO_COMMANDS,
        help="Commands to render. Defaults to all demo commands.",
    )
    return parser.parse_args()


def write_demo_output(output_dir: Path, name: str, text: str, markdown: str, json_text: str) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    text_path = output_dir / f"{name}.txt"
    md_path = output_dir / f"{name}.md"
    json_path = output_dir / f"{name}.json"
    text_path.write_text(text, encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json_text, encoding="utf-8")
    return {"text": str(text_path), "markdown": str(md_path), "json": str(json_path)}


def main() -> None:
    args = parse_args()
    service = BotService(
        driver=args.driver,
        compare_user_csv=args.user_csv,
        compare_benchmark_csv=args.benchmark_csv,
        output_dir=args.output_dir,
    )
    runner = BotCommandRunner(service)

    generated: dict[str, dict[str, str]] = {}
    for command in args.commands:
        kwargs = {"driver": args.driver}
        if command == "compare":
            kwargs.update(
                {
                    "user_csv": args.user_csv,
                    "benchmark_csv": args.benchmark_csv,
                    "output_dir": args.output_dir / "compare",
                }
            )
        execution = runner.render(command, **kwargs)
        generated[command] = write_demo_output(args.output_dir, command if command != "telemetry" else f"telemetry_{args.driver}", execution.text, execution.markdown, execution.json_text)
        print(execution.text)
    index_lines = ["Bot demo outputs", "=================", ""]
    for command, files in generated.items():
        index_lines.append(f"{command}: {files['markdown']}")
        index_lines.append(f"      {files['json']}")
        index_lines.append(f"      {files['text']}")
    (args.output_dir / "index.txt").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"\nSaved demo artifacts under {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
