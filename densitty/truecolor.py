"""ANSI "True color" (24b, 16M colors) support."""

import operator
import math

from itertools import islice
from typing import Optional, Sequence, overload

from . import ansi
from .util import FloatLike, clamp, quantize

# Note: by default, we usethe widely supported 38;2;R;G;B to set foreground color
# An alternate spec is ODA which is 38:2::R:G:B (NB: colons rather than semicolons).
# The default (semicolons) is not nicely backwards-compatible, since the R;G;B appear
# to be control codes, and can e.g. turn on underline. But it is more widely supported.

# pylint: disable=invalid-name
# User can override this to use ODA codes if desired
use_oda_colorcodes = False

# Probably overkill: linear interpolation of RGB values gets muddy in the middle.
#    Interpolating in CIE "L*a*b*" space typically gives much nicer results.

# ANSI color codes will want RGB values in 0-255 range, Sixels want 0-100.
# So our base RGB triples will be floats ranging 0.0..1.0

# Sixel images can use a palette of up to 256 colors (I think this is widely supported).
# We reserve two colors for FG/BG of axis ticks. To reduce banding in non-sixel images,
# we'll use a more extensive color scale size by default, but downselect for sixels.
NUM_RESERVED_PALETTE_COLORS = 2
DEFAULT_PALETTE_SIZE = 256 - NUM_RESERVED_PALETTE_COLORS
DEFAULT_COLORMAP_SIZE = DEFAULT_PALETTE_SIZE * 2

# To keep the types distinct between LAB triples and RGB triples, we'll make them
# separate types. Trying to use NewType type aliases for RGB/LAB/RGB255 confuses pylint
# so here just use explicit classes, with likely a slight performance penalty.
# And to make interpolation straightforward, define a simplistic
# vector class that can do vector addition and scalar multiplication:


class Vec(tuple[FloatLike, FloatLike, FloatLike]):
    """Class for color component triples (RGB, LAB) to allow for interpolation"""

    def __add__(self, other):
        return Vec((x + y for x, y in zip(self, other)))

    def __mul__(self, mult):
        return Vec((x * mult for x in self))


class RGB(Vec):
    """R/G/B channels with float [0..1] in each"""


class LAB(Vec):
    """L*a*b* channels"""


class RGB255(tuple[int, int, int]):
    """R/G/B channels with 0-255 in each"""


def rgb255(rgb: RGB) -> RGB255:
    """Convert RGB to RGB255"""
    return RGB255((round(rgb[0] * 255), round(rgb[1] * 255), round(rgb[2] * 255)))


def clamp_rgb(rgb: RGB):
    """Returns closest valid RGB value"""
    return RGB(Vec(clamp(x, 0, 1.0) for x in rgb))


@overload
def interp(piecewise: Sequence[RGB], x: float) -> RGB: ...
@overload
def interp(piecewise: Sequence[LAB], x: float) -> LAB: ...


def interp(piecewise: Sequence[Vec], x: float) -> Vec:
    """Evaluate a piecewise linear function, i.e. interpolate between the two closest values.
    Parameters
    ----------
    piecewise: Sequence[RGB] or Sequence[LAB]
               Evenly spaced function values. piecewise[0] := f(0.0), piecewise[-1] := f(1.0)
    x:         float
               value between 0.0 and 1.0
    returns:   RGB or LAB
               f(x)
    """
    max_idx = len(piecewise) - 1
    float_idx = x * max_idx
    lower_idx = math.floor(float_idx)

    if lower_idx < 0:
        return piecewise[0]
    if lower_idx + 1 > max_idx:
        return piecewise[-1]
    frac = float_idx - lower_idx
    lower = piecewise[lower_idx]
    upper = piecewise[lower_idx + 1]
    return lower * (1.0 - frac) + upper * frac


def _rgb_to_linear_rgb(channel):
    """Gamma correction: Convert RGB to 'linear' RGB with gamma of 2.4."""
    if channel > 0.04045:
        return math.pow((channel + 0.055) / 1.055, 2.4)
    return channel / 12.92


def _linear_rgb_to_rgb(channel):
    """Inverse gamma correction: Convert 'linear' RGB back to RGB."""
    if channel > 0.0031308:
        return clamp(1.055 * math.pow(channel, 1.0 / 2.4) - 0.055, 0, 1.0)
    return clamp(12.92 * channel, 0, 1.0)


def _vector_transform(v, m):
    """Returns v * m, where v is a vector and m is a matrix (list of columns)."""
    return [sum(map(operator.mul, v, col)) for col in m]


def _rgb_to_lab(rgb: RGB) -> LAB:
    """Convert RGB triple to CIE LAB triple."""

    linear_rgb = tuple(map(_rgb_to_linear_rgb, rgb))
    # Conversion to XYZ that also includes white point calibration of [0.95047, 1.00000, 1.08883]
    linear_rgb_to_xyzn = [
        [0.43394994055572506, 0.376209769903311, 0.18984028954096394],
        [0.2126729, 0.7151522, 0.072175],
        [0.01775658275396527, 0.10946796102238184, 0.8727754562236529],
    ]
    xyzn = _vector_transform(linear_rgb, linear_rgb_to_xyzn)

    def f(t):
        """common part of xyz->lab transform"""
        if t > 0.008856451679035631:
            return math.pow(t, 1 / 3)
        return 0.13793103448275862 + t / 0.12841854934601665

    fxyz = tuple(map(f, xyzn))

    lum = 116 * fxyz[1] - 16
    a = 500 * (fxyz[0] - fxyz[1])
    b = 200 * (fxyz[1] - fxyz[2])
    return LAB((lum, a, b))


def _lab_to_rgb(lab: LAB) -> RGB:
    """Convert CIE LAB triple to RGB."""

    fy = (lab[0] + 16) / 116
    fx = lab[1] / 500 + fy
    fz = fy - lab[2] / 200

    def f_inv(t):
        if t > 0.20689655172413793:
            return t**3
        return 0.12841854934601665 * (t - 0.13793103448275862)

    xyzn = (f_inv(fx), f_inv(fy), f_inv(fz))

    # Conversion from XYZ that also includes the white point calibration/normalization:
    xyzn_to_linear_rgb = [
        [3.079954503474, -1.5371385, -0.542815944262],
        [-0.92125825502, 1.8760108, 0.04524741948],
        [0.052887382398000005, -0.2040259, 1.151138514516],
    ]
    linear_rgb = _vector_transform(xyzn, xyzn_to_linear_rgb)

    rgb = tuple(map(_linear_rgb_to_rgb, linear_rgb))
    return RGB(rgb)


def expand_rgb_colormap(color_points: Sequence[RGB], num_output_colors=256, interp_in_rgb=False):
    """Expand a list of RGB colors by interpolation"""
    if interp_in_rgb:
        return tuple(
            clamp_rgb(interp(color_points, x / (num_output_colors - 1)))
            for x in range(num_output_colors)
        )

    # Convert to CIE Lab, interpolate there, and convert back to RGB
    lab_color_points = tuple(_rgb_to_lab(point) for point in color_points)
    lab_scale = [
        interp(lab_color_points, x / (num_output_colors - 1)) for x in range(num_output_colors)
    ]
    return tuple(clamp_rgb(_lab_to_rgb(point)) for point in lab_scale)


class Colormap_24b:
    """Can be called as if it were a function to produce ANSI codes, returning ANSI colors
    interpolated from the provided sequence.
    Can also be used as an RGB colormap for sixels.
    """

    # If using sixels, there will be a max of # colors in used in palette (256, minus reserved
    # FG/BG colors for axis ticks). To make things work nicely, use a multiple of
    # DEFAULT_PALETTE_SIZE by default.

    def __init__(
        self,
        color_points: Sequence[RGB],
        num_output_colors=2 * DEFAULT_PALETTE_SIZE,
        interp_in_rgb=False,
    ):
        """
        Parameters
        ----------
        color_points: Sequence[Vec]
                      Evenly-spaced color values corresponding to 0.0..1.0
        num_output_colors: int
                      Number of distinct interpolated output colors to use
                      Default: 2 * max number of colors in sixel palette
        interp_in_rgb: bool
                      Interpolate in RGB space rather than Lab space
        """
        self.count = num_output_colors
        self.scale = expand_rgb_colormap(color_points, num_output_colors, interp_in_rgb)
        self.palette_size = min(num_output_colors, DEFAULT_PALETTE_SIZE)
        self.palette_stride = math.ceil(num_output_colors / self.palette_size)

    def __call__(self, bg_frac: Optional[float], fg_frac: Optional[float]):
        """Using the colormap object as a function, so it can be used with Plot class"""
        codes = []
        if fg_frac is not None:
            fg_idx = quantize(fg_frac, self.count)
            fg = rgb255(self.scale[fg_idx])
            if use_oda_colorcodes:
                codes += [f"38:2::{fg[0]}:{fg[1]}:{fg[2]}"]
            else:
                codes += [f"38;2;{fg[0]};{fg[1]};{fg[2]}"]
        if bg_frac is not None:
            bg_idx = quantize(bg_frac, self.count)
            bg = rgb255(self.scale[bg_idx])
            if use_oda_colorcodes:
                codes += [f"48:2::{bg[0]}:{bg[1]}:{bg[2]}"]
            else:
                codes += [f"48;2;{bg[0]};{bg[1]};{bg[2]}"]
        return ansi.compose(codes)

    def palette(self, axis_fg: RGB, axis_bg: RGB):
        """For sixel support: returns a list of colors by index"""
        scale_palette = islice(self.scale, 0, None, self.palette_stride)
        return (axis_bg, axis_fg, *scale_palette)

    def from_palette(self, frac):
        """For sixel support: turn 0..1 into a color index"""
        idx = clamp(math.floor(frac * self.palette_size), 0, self.palette_size - 1)
        return idx + NUM_RESERVED_PALETTE_COLORS


# RGB Color triples to use in making color scales:
BLACK = RGB((0, 0, 0))
WHITE = RGB((1.0, 1.0, 1.0))
RED = RGB((1.0, 0, 0))
GREEN = RGB((0, 1.0, 0))
BLUE = RGB((0, 0, 1.0))
YELLOW = RGB((1.0, 1.0, 0))
ORANGE = RGB((1.0, 0.5, 0))
CYAN = RGB((0, 1.0, 1.0))
PURPLE = RGB((0.4, 0, 0.4))
MAGENTA = RGB((1.0, 0, 1.0))

# pylint: disable=invalid-name
# Black -> White, interpolating in RGB
GRAYSCALE_FAST = Colormap_24b([BLACK, WHITE], interp_in_rgb=True)

# More uniform gradation of lightness across the scale:
GRAYSCALE = Colormap_24b([BLACK, WHITE])

# Blue->Red
BLUE_RED = Colormap_24b([BLUE, RED])

RAINBOW = Colormap_24b([RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE])

REV_RAINBOW = Colormap_24b([PURPLE, BLUE, CYAN, GREEN, YELLOW, ORANGE, RED])

# Starting from black, fade into reverse rainbow:
FADE_IN = Colormap_24b([BLACK, PURPLE, BLUE, CYAN, GREEN, YELLOW, ORANGE, RED])

HOT = Colormap_24b([BLACK, RED, ORANGE, YELLOW, WHITE])

COOL = Colormap_24b([CYAN, MAGENTA])
