"""Visual diff utility for golden test outputs."""

from __future__ import annotations

import argparse
import ast
import re
import sys

from itertools import zip_longest
from pathlib import Path
from typing import Iterable

import readchar

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
ANSI_LEADINGCOLOR_RE = re.compile(r"^(\x1b\[[^m]*m.)(.*)$")
MAX_LITERAL_LENGTH = 200_000
MIN_MARKER_LENGTH = 1


def strip_ansi(value: str) -> str:
    """Remove ANSI escape sequences."""
    return ANSI_ESCAPE_RE.sub("", value)

def split_ansi(value: str) -> str:
    """Split into list, each element is a single character or color + character."""
    out, remaining = [], value
    while remaining:
        match = ANSI_LEADINGCOLOR_RE.match(remaining)
        if match is None:
            out += [remaining[0]]
            remaining = remaining[1:]
        else:
            out += [match[1]]
            remaining = match[2]
    return out


def parse_lines(raw_text: str) -> list[str]:
    """Convert the stored golden text into displayable lines."""
    if len(raw_text) > MAX_LITERAL_LENGTH:
        parsed = raw_text
    else:
        try:
            parsed = ast.literal_eval(raw_text)
        except (ValueError, SyntaxError):
            parsed = raw_text

    if isinstance(parsed, (tuple, list)):
        values = [str(item) for item in parsed]
    else:
        values = [str(parsed)]

    lines: list[str] = []
    for value in values:
        split_lines = value.splitlines()
        if split_lines:
            lines.extend(split_lines)
        else:
            lines.append("")
    return lines or [""]


def marker_line(golden_line: str, new_line: str) -> str:
    """Create a per-character marker string highlighting changed positions.

    ^ : visible character changed
    ~ : only ANSI/color codes changed
    """

    visible_golden = strip_ansi(golden_line)
    visible_new = strip_ansi(new_line)

    max_len = max(len(visible_golden), len(visible_new))
    if golden_line != new_line and visible_golden == visible_new:
        golden_split = split_ansi(golden_line)
        new_split = split_ansi(new_line)
        as_pairs = zip_longest(golden_split, new_split, fillvalue="")
        diff_list = [" " if x == y else "~" for x,y in as_pairs]
        return "".join(diff_list)

    markers: list[str] = []
    for idx in range(max_len):
        golden_char = visible_golden[idx] if idx < len(visible_golden) else ""
        new_char = visible_new[idx] if idx < len(visible_new) else ""
        markers.append("^" if golden_char != new_char else " ")

    return "".join(markers)


def visual_diff(golden_lines: Iterable[str], new_lines: Iterable[str]) -> list[str]:
    """Build a human-friendly diff for the provided line sequences."""
    output: list[str] = []
    for idx, (golden_line, new_line) in enumerate(
        zip_longest(golden_lines, new_lines, fillvalue="")
    ):
        if golden_line == new_line:
            continue
        markers = marker_line(golden_line, new_line)
        output.append(f"line {idx + 1}:")
        output.append(f"  gold: {golden_line}")
        output.append(f"   new: {new_line}")
        if markers.strip():
            output.append(f"  diff: {markers}")
    return output


def compare_pair(golden_path: Path, new_path: Path) -> str:
    """Create a visual diff report for a single file pair."""
    golden_lines = parse_lines(golden_path.read_text())
    new_lines = parse_lines(new_path.read_text())
    diff_lines = visual_diff(golden_lines, new_lines)
    if not diff_lines:
        body = ["No differences detected."]
    else:
        body = diff_lines
    return "\n".join(body)


def process_new_goldens(golden_dir: Path, new_dir: Path) -> str:
    """Iterate through all new/updated golden files, showing diff and taking user-specified action"""
    if not new_dir.exists():
        return f"No new goldens found at {new_dir}"

    files = sorted([path for path in new_dir.iterdir() if path.is_file()])
    if not files:
        return f"No new goldens found at {new_dir}"

    for new_path in files:
        golden_path = golden_dir / new_path.name
        if not golden_path.exists():
            print(f"\n=== {new_path.name} ===\nDoes not have an existing golden file")
        else:
            print(f"\n=== {new_path.name} ===")
            print(compare_pair(golden_path, new_path))
        while True:
            print("(a)ccept, (d)ecline, (s)kip, (q)uit: ", end="", flush=True)

            key = readchar.readchar()
            print(key)
            if key == "a":
                new_path.replace(golden_path)
                break
            if key == "d":
                new_path.unlink()
                break
            if key == "s":
                break
            if key == "q":
                sys.exit(0)


def test_marker_line_highlights_character_changes():
    assert marker_line("abc", "axc") == " ^ "


def test_marker_line_marks_color_only_differences():
    red = "aaa\x1b[31mx\x1b[0mbbb\x1b[31mX\x1b[0mccc"
    green = "aaa\x1b[32mx\x1b[0mbbb\x1b[32mX\x1b[0mccc"
    marker = marker_line(red, green)
    assert marker == "   ~   ~   "


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
    assert "gold: abc" in report
    assert " new: axc" in report
    assert "diff:  ^" in report
    assert "line 2:" not in report

if __name__ == "__main__":
    process_new_goldens(Path("tests/goldens"), Path("tests/new_goldens"))
