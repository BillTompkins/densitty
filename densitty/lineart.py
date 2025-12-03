"""Unicode/ASCII line-art support."""

from itertools import zip_longest
from typing import Any

# For Y axis fractional tick marks when there is a border line, we can try to use Unicode combining
# characters to put a tick at the top/bottom of the "│" border, like:
#
# "│̅" or "│̲"
#
# Terminal emulators support for this seems poor though.
#
# iTerm2 3.5.11: A modified/combined "│" gets shifted slightly to the left
#                so using the resulting left border look janky.
# Apple Terminal 2.14: Vertical parts are aligned. Combining under/over line with vertical
#                have a different height than when combined with space, but that is likely ok
#                for us.
# Alacritty 0.16.1: Vertical/Horizontal alignment is great! But low/high is shifted to the right?
#
# At present, probably not worth trying to use this in general, but leaving the code in place

COMBINING_OVERLINE = "\u0305"  # Unicode Combining Overline, modifies previous character
COMBINING_LOWLINE = "\u0332"  # Unicode Combining Low Line, modifies previous character


# Translations of Unicode line-art / block characters in case they aren't present in the font:

ascii_font = str.maketrans(
    {
        "─": "-",
        # For half-lines, we could render either as full lines or as nothing
        # Since they will only show up as overhangs on the end of an axis,
        # just opt for nothing for now.
        # "╴": "-",
        # "╶": "-",
        "╴": " ",
        "╶": " ",
        "│": "|",
        # "╵": "|",
        # "╷": "|",
        "╵": " ",
        "╷": " ",
        "▁": "_",
        "▔": "/",
        "┼": "+",
        "┐": "+",
        "┌": "+",
        "└": "+",
        "┘": "+",
    }
)

# Some line-art glyphs are less common, so have a mapping that translates just them:
basic_font = str.maketrans({"▁": "_", "▔": "/", "╴": " ", "╶": " ", "╵": " ", "╷": " "})

extended_font: dict[Any, Any] = {}  # a do-nothing translation

strip_combining = str.maketrans({COMBINING_LOWLINE: "", COMBINING_OVERLINE: ""})

flip_vertical = str.maketrans(
    {
        "╱": "╲",
        "╲": "╱",
        "┌": "└",
        "└": "┌",
        "┐": "┘",
        "┘": "┐",
        "┴": "┬",
        "┬": "┴",
        "╷": "╵",
        "╵": "╷",
        "▔": "▁",
        "▁": "▔",
        COMBINING_LOWLINE: COMBINING_OVERLINE,
        COMBINING_OVERLINE: COMBINING_LOWLINE,
    }
)

line_char_arms = {  # map line-art chars to sets of Left/Up/Down/Right arms:
    " ": frozenset(),
    "╷": frozenset("D"),
    "╴": frozenset("L"),
    "╶": frozenset("R"),
    "╵": frozenset("U"),
    "│": frozenset("DU"),
    "┐": frozenset("DL"),
    "┌": frozenset("DR"),
    "─": frozenset("LR"),
    "┘": frozenset("LU"),
    "└": frozenset("RU"),
    "┴": frozenset("LRU"),
    "┤": frozenset("LDU"),
    "┬": frozenset("DLR"),
    "├": frozenset("DRU"),
    "┼": frozenset("DLRU"),
}

reverse_line_char_arms = {v: k for k, v in line_char_arms.items()}

combinable = {"▁": COMBINING_LOWLINE, "▔": COMBINING_OVERLINE}


def merge_chars(a: str, b: str, use_combining_unicode: bool = False) -> str:
    """Merge two line-art characters into a single character"""
    if use_combining_unicode and a in combinable:
        return b + combinable[a]

    if use_combining_unicode and b in combinable:
        return a + combinable[b]

    if b not in line_char_arms:
        return b
    if a not in line_char_arms:
        return a

    all_arms = line_char_arms[a] | line_char_arms[b]
    return reverse_line_char_arms[all_arms]


def merge_lines(line_a: str, line_b: str, use_combining_unicode: bool = False) -> str:
    """Merge two lines with line-art characters into a single line"""
    return "".join(
        merge_chars(a, b, use_combining_unicode)
        for a, b in zip_longest(line_a, line_b, fillvalue=" ")
    )


def display_len(line: str) -> int:
    """Calculate the display length of a string, ignoring combining characters"""
    return len(line.translate(strip_combining))
