"""Visual diff utility for golden test outputs."""

from __future__ import annotations

import argparse
import ast
import re
from itertools import zip_longest
from pathlib import Path
from typing import Iterable


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
MAX_LITERAL_LENGTH = 200_000
MIN_MARKER_LENGTH = 1


def strip_ansi(value: str) -> str:
    """Remove ANSI escape sequences."""
    return ANSI_ESCAPE_RE.sub("", value)


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
        color_only_length = max(
            len(golden_line),
            len(new_line),
            len(visible_golden),
            len(visible_new),
            MIN_MARKER_LENGTH,
        )
        return "~" * color_only_length

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
        output.append(f"  golden: {golden_line}")
        output.append(f"  new: {new_line}")
        if markers.strip():
            output.append(f"  diff: {markers}")
    return output


def compare_pair(name: str, golden_path: Path, new_path: Path) -> str:
    """Create a visual diff report for a single file pair."""
    golden_lines = parse_lines(golden_path.read_text())
    new_lines = parse_lines(new_path.read_text())
    diff_lines = visual_diff(golden_lines, new_lines)
    if not diff_lines:
        body = ["No differences detected."]
    else:
        body = diff_lines
    return "\n".join([f"=== {name} ===", *body])


def build_report(golden_dir: Path, new_dir: Path) -> str:
    """Generate a report for all new golden files."""
    if not new_dir.exists():
        return f"No new goldens found at {new_dir}"

    files = sorted([path for path in new_dir.iterdir() if path.is_file()])
    if not files:
        return f"No new goldens found at {new_dir}"

    sections = []
    for new_path in files:
        golden_path = golden_dir / new_path.name
        if not golden_path.exists():
            sections.append(
                f"=== {new_path.name} ===\nMissing golden file at {golden_path}"
            )
            continue
        sections.append(compare_pair(new_path.name, golden_path, new_path))

    return "\n\n".join(sections)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare tests/new_goldens against tests/goldens and show a visual diff "
            "of changed elements."
        )
    )
    parser.add_argument(
        "--goldens",
        type=Path,
        default=Path("tests/goldens"),
        help="Directory containing existing golden outputs.",
    )
    parser.add_argument(
        "--new-goldens",
        dest="new_goldens",
        type=Path,
        default=Path("tests/new_goldens"),
        help="Directory containing newly generated golden outputs.",
    )
    args = parser.parse_args(argv)
    print(build_report(args.goldens, args.new_goldens))


if __name__ == "__main__":
    main()
