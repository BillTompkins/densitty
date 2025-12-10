"""ANSI "True color" (24b, 16M colors) support."""

import math

from typing import Optional, Sequence

from . import ansi
from .util import clamp, clamp_rgb, interp, Vec

# Note: by default, we usethe widely supported 38;2;R;G;B to set foreground color
# An alternate spec is ODA which is 38:2::R:G:B (NB: colons rather than semicolons).
# The default (semicolons) is not nicely backwards-compatible, since the R;G;B appear
# to be control codes, and can e.g. turn on underline. But it is more widely supported.

# pylint: disable=invalid-name
# User can override this to use ODA codes if desired
use_oda_colorcodes = False

# Probably overkill: linear interpolation of RGB values gets muddy in the middle.
#    Interpolating in CIE "L*a*b*" space typically gives much nicer results.


def _rgb_to_linear_rgb(channel):
    """Gamma correction: Convert RGB to 'linear' RGB with gamma of 2.4."""
    channel = channel / 255.0
    if channel > 0.04045:
        return math.pow((channel + 0.055) / 1.055, 2.4)
    return channel / 12.92


def _linear_rgb_to_rgb(channel):
    """Inverse gamma correction: Convert 'linear' RGB back to RGB."""
    if channel > 0.0031308:
        return clamp(round(255 * 1.055 * math.pow(channel, 1.0 / 2.4) - 0.055), 0, 255)
    return clamp(round(255 * 12.92 * channel), 0, 255)


def _vector_transform(v, m):
    """Returns v * m, where v is a vector and m is a matrix (list of columns)."""
    return [math.sumprod(v, col) for col in m]


def _rgb_to_lab(rgb: Vec) -> Vec:
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
    return (lum, a, b)


def _lab_to_rgb(lab: Vec) -> Vec:
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
    return rgb


def colormap_24b(color_points: Sequence[Vec], num_output_colors=256, interp_in_rgb=False):
    """Produce a function that returns ANSI colors interpolated from the provided sequence
    Parameters
    ----------
    color_points: Sequence[Vec]
                  Evenly-spaced color values corresponding to 0.0..1.0
    num_output_colors: int
                  Number of distinct interpolated output colors to use
    interp_in_rgb: bool
                  Interpolate in RGB space rather than Lab space
    """
    # create the color map by interpolating between the given color points
    if interp_in_rgb:
        scale = tuple(
            clamp_rgb(interp(color_points, x / (num_output_colors - 1)))
            for x in range(num_output_colors)
        )
    else:
        lab_color_points = tuple(_rgb_to_lab(point) for point in color_points)
        lab_scale = [
            interp(lab_color_points, x / (num_output_colors - 1)) for x in range(num_output_colors)
        ]
        scale = tuple(clamp_rgb(_lab_to_rgb(point)) for point in lab_scale)

    def colorcode(bg_frac: Optional[float], fg_frac: Optional[float]):
        codes = []
        if fg_frac is not None:
            fg_idx = clamp(round(fg_frac * num_output_colors), 0, num_output_colors - 1)
            if use_oda_colorcodes:
                codes += [f"38:2::{scale[fg_idx][0]}:{scale[fg_idx][1]}:{scale[fg_idx][2]}"]
            else:
                codes += [f"38;2;{scale[fg_idx][0]};{scale[fg_idx][1]};{scale[fg_idx][2]}"]
        if bg_frac is not None:
            bg_idx = clamp(round(bg_frac * num_output_colors), 0, num_output_colors - 1)
            if use_oda_colorcodes:
                codes += [f"48:2::{scale[bg_idx][0]}:{scale[bg_idx][1]}:{scale[bg_idx][2]}"]
            else:
                codes += [f"48;2;{scale[bg_idx][0]};{scale[bg_idx][1]};{scale[bg_idx][2]}"]
        return ansi.compose(codes)

    return colorcode


# RGB Color triples to use in making color scales:
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
CYAN = (0, 255, 255)
PURPLE = (102, 0, 102)
MAGENTA = (255, 0, 255)


# pylint: disable=invalid-name
# (0,0,0), (1,1,1), (2,2,2)...(255,255,255):
GRAYSCALE = colormap_24b([BLACK, WHITE], interp_in_rgb=True)

# More uniform gradation of lightness across the scale:
GRAYSCALE_LINEAR = colormap_24b([BLACK, WHITE], num_output_colors=512)

# Blue->Red
BLUE_RED = colormap_24b([BLUE, RED])

RAINBOW = colormap_24b([RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE])

REV_RAINBOW = colormap_24b([PURPLE, BLUE, CYAN, GREEN, YELLOW, ORANGE, RED])

# Starting from black, fade into reverse rainbow:
FADE_IN = colormap_24b([BLACK, PURPLE, BLUE, CYAN, GREEN, YELLOW, ORANGE, RED])

HOT = colormap_24b([BLACK, RED, ORANGE, YELLOW, WHITE])

COOL = colormap_24b([CYAN, MAGENTA])
