"""Read construction tasks from CSV and draw them as a text or SVG Gantt chart."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from html import escape
from pathlib import Path


@dataclass(frozen=True)
class Task:
    """One task with an inclusive start and end date."""

    name: str
    start: date
    end: date

    @property
    def days(self) -> int:
        """Length in calendar days, counting both ends."""
        return (self.end - self.start).days + 1


def load(path: str | Path) -> list[Task]:
    """Read tasks from a CSV with columns name,start,end (YYYY-MM-DD)."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for col in ("name", "start", "end"):
            if col not in (reader.fieldnames or []):
                raise ValueError(f"missing column: {col}")
        tasks = []
        for n, row in enumerate(reader, start=2):
            try:
                start = date.fromisoformat(row["start"].strip())
                end = date.fromisoformat(row["end"].strip())
            except ValueError as exc:
                raise ValueError(f"line {n}: bad date ({exc})") from exc
            if end < start:
                raise ValueError(f"line {n}: end is before start")
            tasks.append(Task(row["name"].strip(), start, end))
    if not tasks:
        raise ValueError("no tasks in file")
    return sorted(tasks, key=lambda t: (t.start, t.end))


def span(tasks: list[Task]) -> tuple[date, date]:
    """First start and last end across all tasks."""
    return min(t.start for t in tasks), max(t.end for t in tasks)


def text_chart(tasks: list[Task], width: int = 60) -> str:
    """Draw a text chart. Each column covers one or more days so the chart fits width."""
    first, last = span(tasks)
    total = (last - first).days + 1
    cols = min(total, width)
    per_col = total / cols
    label = max(len(t.name) for t in tasks)
    lines = [f"{'':<{label}}  {first.isoformat()} to {last.isoformat()}  ({total} days, "
             f"{per_col:.1f} day(s) per column)"]
    for t in tasks:
        a = int((t.start - first).days / per_col)
        b = max(a + 1, int(((t.end - first).days + 1) / per_col + 0.999))
        bar = " " * a + "#" * (min(b, cols) - a)
        lines.append(f"{t.name:<{label}}  |{bar:<{cols}}| {t.days}d")
    return "\n".join(lines)


def svg_chart(tasks: list[Task], day_px: int = 12, row_px: int = 26) -> str:
    """Return an SVG document with one bar per task and a tick every Monday."""
    first, last = span(tasks)
    total = (last - first).days + 1
    left = 10 + 7 * max(len(t.name) for t in tasks)
    width = left + total * day_px + 20
    height = 40 + row_px * len(tasks)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'font-family="monospace" font-size="12">',
           f'<rect width="{width}" height="{height}" fill="white"/>']
    for d in range(total):
        day = first + timedelta(days=d)
        if day.weekday() == 0:
            x = left + d * day_px
            out.append(f'<line x1="{x}" y1="28" x2="{x}" y2="{height}" stroke="#ddd"/>')
            out.append(f'<text x="{x + 2}" y="20">{day.strftime("%m/%d")}</text>')
    for i, t in enumerate(tasks):
        y = 36 + i * row_px
        x = left + (t.start - first).days * day_px
        out.append(f'<text x="5" y="{y + 14}">{escape(t.name)}</text>')
        out.append(f'<rect x="{x}" y="{y}" width="{t.days * day_px}" height="18" fill="#3b7dd8"/>')
    out.append("</svg>")
    return "\n".join(out)
