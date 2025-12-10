from pathlib import Path

from densitty.golden_diff import build_report, marker_line


def test_marker_line_highlights_character_changes():
    assert marker_line("abc", "axc") == " ^ "


def test_marker_line_marks_color_only_differences():
    red = "\x1b[31mx\x1b[0m"
    green = "\x1b[32mx\x1b[0m"
    marker = marker_line(red, green)
    assert set(marker) == {"~"}
    assert len(marker) == len(red)


def test_build_report_describes_changed_lines(tmp_path: Path):
    goldens = tmp_path / "goldens"
    goldens.mkdir()
    new_goldens = tmp_path / "new_goldens"
    new_goldens.mkdir()

    (goldens / "sample").write_text("('abc', '123')")
    (new_goldens / "sample").write_text("('axc', '123')")

    report = build_report(goldens, new_goldens)

    assert "sample" in report
    assert "line 1:" in report
    assert "golden: abc" in report
    assert "new: axc" in report
    assert "diff:  ^" in report
    assert "line 2:" not in report


def test_build_report_handles_missing_new_directory(tmp_path: Path):
    goldens = tmp_path / "goldens"
    goldens.mkdir()

    report = build_report(goldens, tmp_path / "missing")

    assert "No new goldens found" in report
