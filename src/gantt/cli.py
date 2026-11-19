"""Command line interface."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import core


def main(argv: list[str] | None = None) -> int:
    """Run the tool and return an exit code."""
    parser = argparse.ArgumentParser(prog="gantt", description="Gantt chart from a CSV of tasks.")
    parser.add_argument("csv", help="CSV with columns name,start,end")
    parser.add_argument("--width", type=int, default=60, help="text chart columns (default 60)")
    parser.add_argument("--svg", metavar="FILE", help="also write an SVG chart to FILE")
    args = parser.parse_args(argv)
    if args.width < 1:
        print("error: --width must be at least 1", file=sys.stderr)
        return 2
    try:
        tasks = core.load(args.csv)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(core.text_chart(tasks, args.width))
    if args.svg:
        Path(args.svg).write_text(core.svg_chart(tasks), encoding="utf-8")
        print(f"wrote {args.svg}")
    return 0
