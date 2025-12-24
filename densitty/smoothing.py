"""Creation of 2-D density maps for (x,y) data"""

import math
from bisect import bisect_right
from decimal import Decimal
from typing import Callable, Optional, Sequence

from .axis import Axis
from .binning import calc_value_range, pick_edges
from .util import FloatLike, ValueRange
from .util import clamp, make_decimal, make_value_range, most_round, round_up_ish

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
    def out(delta: tuple[FloatLike, FloatLike]) -> FloatLike:
        return gaussian(delta, inv_sigma)
    return out

# Kernel Density Estimation: Scott's rule: BW = n**(-1/6).  Silverman factor is same for d=2.
# inv_sigma = covariance * BW**2
# invert 2x2: [[d, -b], [-c, a]] / (a*d - b*c)

def triangle(width_x, width_y) -> SmoothingFunc:
    def out(delta: tuple[FloatLike, FloatLike]) -> FloatLike:
        x_factor = max(0.0, width_x / 2 - abs(delta[0]))
        y_factor = max(0.0, width_y / 2 - abs(delta[1]))
        return x_factor * y_factor
    return out


def func_span(f: Callable):
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

def func_width(f: SmoothingFunc):
    def f_x(x):
        return f((x, 0))
    return func_span(f_x)

def func_height(f: SmoothingFunc):
    def f_y(y):
        return f((0, y))
    return func_span(f_y)

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
    out = [ [0] * len(x_centers) for _ in range(len(y_centers)) ]

    # Could optimize by starting at bin closest to each point, and move
    # out until contribution is less than some limit

    for x, y in points:
        x_f, y_f = float(x), float(y)
        for x_idx, bin_x in enumerate(x_centers):
            bin_x_f = float(bin_x)
            for y_idx, bin_y in enumerate(y_centers):
                bin_y_f = float(bin_y)
                contrib = kernel(((x_f - bin_x_f), (y_f - bin_y_f)))
                out[y_idx][x_idx] += contrib
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

    if isinstance(bins, int):
        # we were given a single # of bins
        bins = (bins, bins)

    if isinstance(bins, Sequence) and len(bins) > 2:
        # we were given a single list of bin edges: replicate it
        bins = (bins, bins)

    if isinstance(bins[0], int):
        # we were given the number of bins for X. Calculate the edges:
        if ranges is None or ranges[0] is None:
            x_range = calc_value_range(tuple(x for x, _ in points))
            padding = Decimal(func_width(kernel))
            x_range = ValueRange(x_range[0] - padding, x_range[1] + padding)
        else:
            x_range = ranges[0]

        # re-using the binning 'pick_edges' logic to pick centers, but there is one fewer "center" than edge:
        # TODO: refactor/rename?
        x_centers = pick_edges(bins[0] - 1, x_range, align)
    else:
        # we were given the bin edges already
        if ranges is not None and ranges[0] is not None:
            raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
        assert isinstance(bins[0], Sequence)
        x_centers = bins[0]

    if isinstance(bins[1], int):
        # we were given the number of bins. Calculate the edges:
        if ranges is None or ranges[1] is None:
            y_range = calc_value_range(tuple(y for _, y in points))
            padding = Decimal(func_height(kernel))
            y_range = ValueRange(y_range[0] - padding, y_range[1] + padding)
        else:
            y_range = ranges[1]
        # TODO: Same as X
        y_centers = pick_edges(bins[1] - 1, y_range, align)
    else:
        # we were given the bin edges already
        if ranges is not None and ranges[1] is not None:
            raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
        assert isinstance(bins[1], Sequence)
        y_centers = bins[1]

    x_axis = Axis((x_centers[0], x_centers[-1]), values_are_edges=False, **axis_args)
    y_axis = Axis((y_centers[0], y_centers[-1]), values_are_edges=False, **axis_args)

    return (smooth_to_bins(points, kernel, x_centers, y_centers), x_axis, y_axis)
