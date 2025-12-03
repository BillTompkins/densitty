"""ANSI code/color support"""

# <pedantic> that the 256-color support here is not actually ANSI X3.64, though it uses ANSI-ish
# escape sequences. I believe it was originally done in Xterm. And 4b colors (16-color)
# are really an aixterm extension to the ANSI-specified 8-color standard. </pedantic>

from typing import Optional, Sequence

from .util import nearest


RESET = "\033[0m"


def compose(codes: Sequence[str]) -> str:
    """Given a list of individual color codes, produce the full escape sequence."""
    return f"\033[{';'.join(codes)}m"


def colormap_16(colors):
    """Produce a function that returns closest 4b/16color ANSI color codes from colormap.
    Parameters
    ----------
    colors: Sequence[int]
            Ordered 16-color ANSI colors corresponding to the 0.0..1.0 range
    """

    def as_colorcodes(bg_frac: Optional[float], fg_frac: Optional[float]) -> str:
        """Return ANSI color code for 16-color value(s)
        Parameters
        ----------
        fg_frac: Optional[float]
                 Value 0.0..1.0 for foreground, or None if background-only
        fg_frac: Optional[float]
                 Value 0.0..1.0 for background, or None for foreground-only
        """
        codes = []
        if fg_frac is not None:
            codes += [f"{30 + nearest(colors, fg_frac)}"]
        if bg_frac is not None:
            codes += [f"{40 + nearest(colors, bg_frac)}"]
        return compose(codes)

    return as_colorcodes


def colormap_256(colors):
    """Produce a function that returns closest 8b/256color ANSI color codes from colormap.
    Parameters
    ----------
    colors: Sequence[int]
            Ordered 256-color ANSI colors corresponding to the 0.0..1.0 range
    """

    def as_colorcodes(bg_frac: Optional[float], fg_frac: Optional[float]):
        """Return ANSI color code for 256-color value(s)
        Parameters
        ----------
        fg_frac: Optional[float]
                 Value 0.0..1.0 for foreground, or None if background-only
        fg_frac: Optional[float]
                 Value 0.0..1.0 for background, or None for foreground-only
        """
        codes = []
        if fg_frac is not None:
            fg = nearest(colors, fg_frac)
            codes += [f"38;5;{fg}"]
        if bg_frac is not None:
            bg = nearest(colors, bg_frac)
            codes += [f"48;5;{bg}"]
        return compose(codes)

    return as_colorcodes


########################################################
# Colormaps. Assumed 256-color unless suffixed with _16
# pylint: disable=invalid-name


# ANSI 16-color map colors in ROYGBIV order: Red, Yellow, Green, Cyan, Blue
RAINBOW_16 = colormap_16((5, 1, 3, 2, 6))

# ANSI 16-color 'rainbow', Reversed:
REV_RAINBOW_16 = colormap_16((6, 2, 3, 1, 5))

# ANSI 16-color map colors: Black, Blue, Cyan, Green, Yellow, Red, Magenta, White
FADE_IN_16 = colormap_16((0, 4, 6, 2, 3, 1, 5, 7))

# ANSI 256-color map colors in a grayscale black->white
GRAYSCALE = colormap_256([0] + list(range(232, 256)) + [15])

rainbow_256_colors = (
    # fmt: off
    (196, 202, 208, 214, 220, 190, 154, 118, 82, 46, 47, 48, 43, 80, 81, 39, 27, 21, 56, 91)
    # fmt: on
)
RAINBOW = colormap_256(rainbow_256_colors)
REV_RAINBOW = colormap_256(tuple(reversed(rainbow_256_colors)))

BLUE_RED = colormap_256((21, 56, 91, 126, 161, 196))
FADE_IN = colormap_256(
    # fmt: off
    (16, 53, 54, 55, 56, 57, 21, 21, 27, 39, 81, 80, 43, 48, 47,
     46, 82, 118, 154, 190, 220, 214, 208, 202, 196)
    # fmt: on
)
HOT = colormap_256((16, 52, 88, 124, 160, 196, 202, 208, 214, 220, 226, 227, 228, 229, 230, 231))
COOL = colormap_256((50, 81, 111, 141, 171, 201))
