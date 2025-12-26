"""Creation of 2-D density maps for (x,y) data"""

import math
from typing import Callable, Optional, Sequence

from .axis import Axis
from .binning import calc_value_range, pick_edges, process_bin_args
from .util import FloatLike, ValueRange
from .util import make_decimal

SmoothingFunc = Callable[[FloatLike, FloatLike], FloatLike]

def gaussian(delta: tuple[FloatLike, FloatLike],
             inv_cov: tuple[tuple[FloatLike, FloatLike], tuple[FloatLike, FloatLike]]):
    """Unnormalized Gaussian
    delta: vector of ((x - x0), (y - y0))
    inv_cov: inverse covariance matrix (aka precision)
    """
    exponent = ((delta[0] * delta[0] * inv_cov[0][0]) +
                2 * (delta[0] * delta[1] * inv_cov[0][1]) +
                (delta[1] * delta[1] * inv_cov[1][1]))
    return math.exp(-exponent / 2)

def gaussian_with_sigma(inv_sigma) -> FloatLike:
    """Produce a kernel function for a Gaussian with specified (inverse) width"""
    def out(delta: tuple[FloatLike, FloatLike]) -> FloatLike:
        return gaussian(delta, inv_sigma)
    return out

# Kernel Density Estimation: Scott's rule: BW = n**(-1/6).  Silverman factor is same for d=2.
# inv_sigma = covariance * BW**2
# invert 2x2: [[d, -b], [-c, a]] / (a*d - b*c)

def triangle(width_x, width_y) -> SmoothingFunc:
    """Produce a kernel function for a 2-D triangle with specified width/height"""
    def out(delta: tuple[FloatLike, FloatLike]) -> FloatLike:
        x_factor = max(0.0, width_x / 2 - abs(delta[0]))
        y_factor = max(0.0, width_y / 2 - abs(delta[1]))
        return x_factor * y_factor
    out.widths = (width_x / 2, width_y / 2)
    out.half_height_widths = (width_x / 4, width_y / 4)
    return out


def func_span(f: Callable):
    """Calculate the half-width at half-height of a function"""
    maximum = f(0)
    target = maximum / 2
    # variables 'upper' and 'lower' s.t. f(lower) > maximum/3 and f(upper) < maximum/2
    lower, upper = 0, 1
    # Interval might not contain target, so double 'upper' until it does
    for _ in range(100):
        if  f(upper) <= target:
            break
        lower = upper
        upper *= 2
    else:
        raise ValueError("Unable to compute kernel function half-width")

    # If our initial interval did contain target, the interval may be orders of magnitude too large
    # We'll bisect until 'lower' moves, then bisect 10 times more
    iter_count = 0
    for _ in range(100):
        test = (lower + upper) / 2
        if f(test) < target:
            upper = test
        else:
            lower = test
        if lower > 0:
            iter_count += 1
            if iter_count >= 10:
                break
    else:
        raise ValueError("Unable to compute kernel function half-width")

    return (lower + upper) / 2

def func_width_half_height(f: SmoothingFunc):
    """Provide the (half) width of the function at half height (HWHM)"""

    if "half_height_widths" in dir(f):
        return f.half_height_widths
    # No user-provided width information. Calculate it:
    def f_x(x):
        return f((x, 0))
    def f_y(y):
        return f((0, y))
    return func_span(f_x), func_span(f_y)

def func_width(f: SmoothingFunc):
    """Provide the (half) width of the function that includes nearly all of the area"""

    if "widths" in dir(f):
        return f.widths
    # No user-provided width information. Return 3* the width at half-height
    half_height_width = func_width_half_height(f)
    return (3 * half_height_width[0], 3 * half_height_width[1])


def smooth_to_bins(
    points: Sequence[tuple[FloatLike, FloatLike]],
    kernel: SmoothingFunc,
    x_centers: Sequence[FloatLike],
    y_centers: Sequence[FloatLike],
) -> Sequence[Sequence[int]]:
    """Bin points into a 2-D histogram given bin edges

    Parameters
    ----------
    points:  Sequence of (X,Y) tuples: the data points to smooth
    kernel:  Smoothing Function
    x_centers: Sequence of values: Centers of output columns
    y_centers: Sequence of values: Centers of output rows
    """
    x_ctr_f = [float(x) for x in x_centers]
    y_ctr_f = [float(y) for y in y_centers]

    out = [ [0] * len(x_centers) for _ in range(len(y_centers)) ]

    # Make the assumption that the bin centers are evenly spaced, so we can
    # calculate bin position from index and vice versa
    x_delta = x_ctr_f[1] - x_ctr_f[0]
    y_delta = y_ctr_f[1] - y_ctr_f[0]

    kernel_width, kernel_height = func_width(kernel)
    kernel_width_di = round(kernel_width // x_delta) + 1
    kernel_height_di = round(kernel_height // y_delta) + 1
    for x, y in points:
        x_f, y_f = float(x), float(y)
        ctr_x_i = round((x_f - x_ctr_f[0]) / x_delta)
        start_x_i = ctr_x_i - kernel_width_di
        end_x_i = ctr_x_i + kernel_width_di + 1
        for x_i, bin_x in enumerate(x_ctr_f[start_x_i : end_x_i], start_x_i):
            ctr_y_i = round((y_f - y_ctr_f[0]) / y_delta)
            start_y_i = ctr_y_i - kernel_height_di
            end_y_i = ctr_y_i + kernel_height_di + 1
            for y_i, bin_y in enumerate(y_ctr_f[start_y_i : end_y_i], start_y_i):
                contrib = kernel(((x_f - bin_x), (y_f - bin_y)))
                out[y_i][x_i] += contrib
    return out

def smooth2d(
    points: Sequence[tuple[FloatLike, FloatLike]],
    kernel: SmoothingFunc,
    bins: (
        int
        | tuple[int, int]
        | Sequence[FloatLike]
        | tuple[Sequence[FloatLike], Sequence[FloatLike]]
    ) = 10,
    ranges: Optional[tuple[Optional[ValueRange], Optional[ValueRange]]] = None,
    align=True,
    **axis_args
) -> tuple[Sequence[Sequence[int]], Axis, Axis]:
    """Smooth (x,y) points out into a 2-D Density plot

    Parameters
    ----------
    points: Sequence of (X,Y) tuples: the points to smooth into "bins"
    kernel: SmoothingFunc
                Smoothing function, takes (delta_x, delta_y) and outputs value
    bins: int or (int, int) or [float,...] or ([float,...], [float,...])
                int: number of output rows & columns (default: 10)
                (int,int): number of columns (X), rows (Y)
                list[float]: Column/Row centers
                (list[float], list[float]): column centers for X, column centers for Y
    ranges: Optional (ValueRange, ValueRange)
                ((x_min, x_max), (y_min, y_max)) for the row/column centers if 'bins' is int
                Default: take from data min/max, with buffer based on kernel width
    align: bool (default: True)
                pick bin edges at 'round' values if # of bins is provided
    drop_outside: bool (default: True)
                True: Drop any data points outside the ranges
                False: Put any outside points in closest bin (i.e. edge bins include outliers)
    axis_args: Extra arguments to pass through to Axis constructor

    returns: Sequence[Sequence[int]], (x-)Axis, (y-)Axis
    """

    padding = tuple(map(make_decimal, func_width_half_height(kernel)))

    x_centers, y_centers = process_bin_args(points, bins, ranges, align, False, padding)
    # XXX need to add padding to process_bin_args
    # XXX Should refactor it, make function that does one axis, called twice

    # if isinstance(bins[0], int):
    #     # we were given the number of bins for X. Calculate the edges:
    #     if ranges is None or ranges[0] is None:
    #         x_range = calc_value_range(tuple(x for x, _ in points))
    #         x_range = ValueRange(x_range[0] - padding[0], x_range[1] + padding[0])
    #     else:
    #         x_range = ranges[0]

    #      # re-use the binning 'pick_edges' logic to pick centers,
    #     # but there is one fewer "center" than edge so subtract 1
    #     # TODO: refactor/rename?
    #     x_centers = pick_edges(bins[0] - 1, x_range, align)
    # else:
    #     # we were given the bin edges already
    #     if ranges is not None and ranges[0] is not None:
    #         raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
    #     assert isinstance(bins[0], Sequence)
    #     x_centers = bins[0]

    # if isinstance(bins[1], int):
    #     # we were given the number of bins. Calculate the edges:
    #     if ranges is None or ranges[1] is None:
    #         y_range = calc_value_range(tuple(y for _, y in points))
    #         y_range = ValueRange(y_range[0] - padding[1], y_range[1] + padding[1])
    #     else:
    #         y_range = ranges[1]
    #     # TODO: Same as X
    #     y_centers = pick_edges(bins[1] - 1, y_range, align)
    # else:
    #     # we were given the bin edges already
    #     if ranges is not None and ranges[1] is not None:
    #         raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
    #     assert isinstance(bins[1], Sequence)
    #     y_centers = bins[1]

    x_axis = Axis((x_centers[0], x_centers[-1]), values_are_edges=False, **axis_args)
    y_axis = Axis((y_centers[0], y_centers[-1]), values_are_edges=False, **axis_args)

    return (smooth_to_bins(points, kernel, x_centers, y_centers), x_axis, y_axis)
