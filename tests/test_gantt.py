from datetime import date

import pytest

from gantt import core
from gantt.cli import main


@pytest.fixture
def csv_file(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text("name,start,end\n"
                 "Framing,2026-03-09,2026-03-20\n"
                 "Excavation,2026-03-02,2026-03-06\n"
                 "Roofing,2026-03-23,2026-03-27\n")
    return f


def test_load_sorted_by_start(csv_file):
    assert [t.name for t in core.load(csv_file)] == ["Excavation", "Framing", "Roofing"]


def test_days_inclusive(csv_file):
    assert core.load(csv_file)[0].days == 5


def test_span(csv_file):
    assert core.span(core.load(csv_file)) == (date(2026, 3, 2), date(2026, 3, 27))


def test_missing_column(tmp_path):
    f = tmp_path / "b.csv"
    f.write_text("name,start\nA,2026-01-01\n")
    with pytest.raises(ValueError, match="missing column: end"):
        core.load(f)


def test_bad_date(tmp_path):
    f = tmp_path / "b.csv"
    f.write_text("name,start,end\nA,2026-13-01,2026-01-02\n")
    with pytest.raises(ValueError, match="line 2"):
        core.load(f)


def test_end_before_start(tmp_path):
    f = tmp_path / "b.csv"
    f.write_text("name,start,end\nA,2026-02-01,2026-01-02\n")
    with pytest.raises(ValueError, match="before start"):
        core.load(f)


def test_empty_file(tmp_path):
    f = tmp_path / "b.csv"
    f.write_text("name,start,end\n")
    with pytest.raises(ValueError, match="no tasks"):
        core.load(f)


def test_text_chart_one_column_per_day(csv_file):
    chart = core.text_chart(core.load(csv_file), width=60)
    rows = chart.splitlines()
    assert len(rows) == 4
    assert rows[1].count("#") == 5


def test_text_chart_scales_down(csv_file):
    chart = core.text_chart(core.load(csv_file), width=10)
    assert all(len(r.split("|")[1]) == 10 for r in chart.splitlines()[1:])


def test_svg_contains_bars_and_escapes(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text("name,start,end\nA & B,2026-03-02,2026-03-04\n")
    svg = core.svg_chart(core.load(f))
    assert "A &amp; B" in svg and "<rect" in svg


def test_cli_writes_svg(csv_file, tmp_path, capsys):
    out = tmp_path / "g.svg"
    assert main([str(csv_file), "--svg", str(out)]) == 0
    assert out.read_text().startswith("<svg")


def test_cli_bad_file(capsys):
    assert main(["nope.csv"]) == 2
