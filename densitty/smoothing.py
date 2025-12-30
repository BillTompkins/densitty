"""Creation of 2-D density maps for (x,y) data"""

import dataclasses
import math
from functools import partial, Placeholder
from typing import Callable, Optional, Sequence

from .axis import Axis
from .binning import expand_bins_arg, process_bin_args
from .util import FloatLike, ValueRange

BareSmoothingFunc = Callable[[FloatLike, FloatLike], FloatLike]


@dataclasses.dataclass
class SmoothingFuncWithWidth:
    """Smoothing function plus precalculated widths"""

    func: BareSmoothingFunc
    widths: tuple[FloatLike, FloatLike]  # X & Y widths that include ~99% of weight
    half_height_widths: tuple[FloatLike, FloatLike]  # X & Y widths at half-height

    def __call__(self, delta_x: FloatLike, delta_y: FloatLike) -> FloatLike:
        return self.func(delta_x, delta_y)


SmoothingFunc = BareSmoothingFunc | SmoothingFuncWithWidth


def gaussian(
    delta: tuple[FloatLike, FloatLike],
    inv_cov: tuple[tuple[FloatLike, FloatLike], tuple[FloatLike, FloatLike]],
):
    """Unnormalized Gaussian
    delta: vector of ((x - x0), (y - y0))
    inv_cov: inverse covariance matrix (aka precision)
    """
    exponent = (
        (delta[0] * delta[0] * inv_cov[0][0])
        + 2 * (delta[0] * delta[1] * inv_cov[0][1])
        + (delta[1] * delta[1] * inv_cov[1][1])
    )
    return math.exp(-exponent / 2)


def gaussian_with_sigma(inv_sigma) -> SmoothingFunc:
    """Produce a kernel function for a Gaussian with specified (inverse) width"""

    def out(delta_x: FloatLike, delta_y: FloatLike) -> FloatLike:
        return gaussian((delta_x, delta_y), inv_sigma)

    return out


# Kernel Density Estimation: Scott's rule: BW = n**(-1/6).  Silverman factor is same for d=2.
# inv_sigma = covariance * BW**2
# invert 2x2: [[d, -b], [-c, a]] / (a*d - b*c)


def triangle(width_x, width_y) -> SmoothingFunc:
    """Produce a kernel function for a 2-D triangle with specified width/height"""

    def out(delta_x: FloatLike, delta_y: FloatLike) -> FloatLike:
        x_factor = max(0.0, width_x / 2 - abs(delta_x))
        y_factor = max(0.0, width_y / 2 - abs(delta_y))
        return x_factor * y_factor

    return SmoothingFuncWithWidth(out, (width_x / 2, width_y / 2), (width_x / 4, width_y / 4))


def func_span(f: Callable, fractional_height: FloatLike):
    """Calculate the half-width of function at specified height"""
    maximum = f(0)
    target = maximum * fractional_height
    # variables 'upper' and 'lower' s.t. f(lower) > maximum/3 and f(upper) < maximum/2
    lower, upper = 0.0, 1.0
    # Interval might not contain target, so double 'upper' until it does
    for _ in range(100):
        if f(upper) <= target:
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

    if isinstance(f, SmoothingFuncWithWidth):
        return f.half_height_widths

    # No user-provided width information. Calculate it:
    x_width = func_span(partial(f, Placeholder, 0), 0.5)
    y_width = func_span(partial(f, 0), 0.5)
    return x_width, y_width


def func_width(f: SmoothingFunc):
    """Provide the (half) width of the function that includes nearly all of the area"""

    if isinstance(f, SmoothingFuncWithWidth):
        return f.half_height_widths

    # No user-provided width information. Calculate it.
    # Note: here we're just finding where the function gets down to
    # 1/1000 of max, which neglects that the area scales with the radius from the function center
    # so for very slowly decaying functions (1/r, say) we may be excluding a lot of total weight
    x_width = func_span(partial(f, Placeholder, 0), 0.001)
    y_width = func_span(partial(f, 0), 0.001)
    return x_width, y_width


def smooth_to_bins(
    points: Sequence[tuple[FloatLike, FloatLike]],
    kernel: SmoothingFunc,
    x_centers: Sequence[FloatLike],
    y_centers: Sequence[FloatLike],
) -> Sequence[Sequence[float]]:
    """Bin points into a 2-D histogram given bin edges

    Parameters
    ----------
    points:  Sequence of (X,Y) tuples: the data points to smooth
    kernel:  Smoothing Function
    x_centers: Sequence of values: Centers of output columns
    y_centers: Sequence of values: Centers of output rows
    """
    # pylint: disable=too-many-locals
    x_ctr_f = [float(x) for x in x_centers]
    y_ctr_f = [float(y) for y in y_centers]

    out = [[0.0] * len(x_centers) for _ in range(len(y_centers))]

    # Make the assumption that the bin centers are evenly spaced, so we can
    # calculate bin position from index and vice versa
    x_delta = x_ctr_f[1] - x_ctr_f[0]
    y_delta = y_ctr_f[1] - y_ctr_f[0]

    kernel_width = func_width(kernel)
    # Find width of the kernel in terms of X/Y indexes of the centers:
    kernel_width_di = (
        round(kernel_width[0] // x_delta) + 1,
        round(kernel_width[1] // y_delta) + 1,
    )
    for point in points:
        p = (float(point[0]), float(point[1]))
        min_xi = round((p[0] - x_ctr_f[0]) / x_delta) - kernel_width_di[0]
        min_yi = round((p[1] - y_ctr_f[0]) / y_delta) - kernel_width_di[1]

        for x_i, bin_x in enumerate(x_ctr_f[min_xi : min_xi + 2 * kernel_width_di[0]], min_xi):
            for y_i, bin_y in enumerate(y_ctr_f[min_yi : min_yi + 2 * kernel_width_di[1]], min_yi):
                out[y_i][x_i] += float(kernel((p[0] - bin_x), (p[1] - bin_y)))
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
    **axis_args,
) -> tuple[Sequence[Sequence[float]], Axis, Axis]:
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

    padding = func_width_half_height(kernel)

    expanded_bins = expand_bins_arg(bins)
    x_centers, y_centers = process_bin_args(points, expanded_bins, ranges, align, padding)

    x_axis = Axis((x_centers[0], x_centers[-1]), values_are_edges=False, **axis_args)
    y_axis = Axis((y_centers[0], y_centers[-1]), values_are_edges=False, **axis_args)

    return (smooth_to_bins(points, kernel, x_centers, y_centers), x_axis, y_axis)
