"""Creation of 2-D density maps for (x,y) data"""

import dataclasses
import math
from typing import Callable, Optional, Sequence

from .axis import Axis
from .binning import expand_bins_arg, histogram2d, process_bin_args
from .util import FloatLike, ValueRange, partial_first, partial_second

BareSmoothingFunc = Callable[[FloatLike, FloatLike], FloatLike]


@dataclasses.dataclass
class SmoothingFuncWithWidth:
    """Smoothing function plus precalculated widths"""

    func: BareSmoothingFunc
    # Precalculated widths at certain fractional height (0.5 and 0.001):
    precalc_widths: dict[FloatLike, tuple[FloatLike, FloatLike]]

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


def gaussian_with_inv_cov(inv_cov) -> SmoothingFunc:
    """Produce a kernel function for a Gaussian with specified inverse covariance"""

    def out(delta_x: FloatLike, delta_y: FloatLike) -> FloatLike:
        return gaussian((delta_x, delta_y), inv_cov)

    return out


def gaussian_with_sigmas(sigma_x, sigma_y) -> SmoothingFunc:
    """Produce a kernel function for a Gaussian with specified X & Y widths"""
    inv_cov = ((sigma_x**-2, 0), (0, sigma_y**-2))
    return gaussian_with_inv_cov(inv_cov)


def covariance(points: Sequence[tuple[FloatLike, FloatLike]]):
    """Calculate the covariance matrix of a list of points"""
    num = len(points)
    xs = tuple(x for x, _ in points)
    ys = tuple(y for _, y in points)
    mean_x = sum(xs) / num
    mean_y = sum(ys) / num
    cov_xx = sum((x - mean_x) ** 2 for x in xs) / num
    cov_yy = sum((y - mean_y) ** 2 for y in ys) / num
    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in points) / num
    return ((cov_xx, cov_xy), (cov_xy, cov_yy))


def kde(points: Sequence[tuple[FloatLike, FloatLike]]):
    """Kernel for Kernel Density Estimation
    Note that the resulting smoothing function is quite broad, since the
    covariance estimate converges very slowly.

    This may make sense to use if the distribution of points is itself a
    Gaussian, but makes much less sense if it has any internal structure,
    as that will all get smoothed out.
    """
    # From Scott's rule / Silverman's factor: Bandwidth is n**(-1/6)
    # That is to scale the std deviation (characteristic width)
    # We're using the square of that: (co)variance, so scale by n**(-1/3)
    # And invert to get something we can pass to the gaussian func
    cov = covariance(points)
    scale = len(points) ** (1 / 3)
    scaled_det = scale * (cov[0][0] * cov[1][1] - cov[1][0] * cov[0][1])
    inv_scaled_cov = (
        (cov[1][1] / scaled_det, -cov[0][1] / scaled_det),
        (-cov[1][0] / scaled_det, cov[0][0] / scaled_det),
    )

    return gaussian_with_inv_cov(inv_scaled_cov)


def triangle(width_x, width_y) -> SmoothingFunc:
    """Produce a kernel function for a 2-D triangle with specified width/height
    This is much cheaper computationally than the Gaussian, and gives decent results.
    It has the nice property that if the widths are multiples of the output "bin" size,
    the total output weight is independent of the exact alignment of the output bins.
    """

    def out(delta_x: FloatLike, delta_y: FloatLike) -> FloatLike:
        x_factor = max(0.0, width_x / 2 - abs(delta_x))
        y_factor = max(0.0, width_y / 2 - abs(delta_y))
        return x_factor * y_factor

    return SmoothingFuncWithWidth(
        out,
        {
            0.5: (width_x / 4, width_y / 4),
            0.001: (width_x / 2, width_y / 2),
        },
    )


def pick_kernel_bandwidth(
    points: Sequence[tuple[FloatLike, FloatLike]],
    bins: tuple[int, int],
    ranges: Optional[tuple[Optional[ValueRange], Optional[ValueRange]]] = None,
    smoothness: FloatLike = 3,
    smooth_fraction: FloatLike = 0.5,
) -> tuple[float, float]:
    """Determine an 'optimal' width for a kernel based on histogram binning

    Parameters
    ----------
    points: Sequence of X,Y points each should be (float, float)
    bins: tuple(int, int)
            expected output number of columns/rows in plot
            so kernel will at least be on the order of one bin
    ranges: optional tuple of ValueRanges
            expected output plot range. Determined from data if unset.
    smoothness: float
            Number of points in a histogram bin that is deemed "smooth"
            1: minumum smoothing. 3 gives reasonable results.
    smooth_fraction: float (fraction 0.0..1.0)
            fraction of non-zero bins that must have the desired smoothness
            0.5 => median non-zero bin
    """
    if bins[0] <= 0 or bins[1] <= 0:
        raise ValueError("Number of bins must be nonzero")

    while bins[0] > 0 and bins[1] > 0:
        binned, x_axis, y_axis = histogram2d(points, bins, ranges, align=False)
        nonzero_bins = [b for row in binned for b in row if b > 0]
        test_pos = int(len(nonzero_bins) * (1.0 - smooth_fraction))
        test_val = sorted(nonzero_bins)[test_pos]
        if test_val >= smoothness:
            break
        bins = (bins[0] - 1, bins[1] - 1)
    else:
        # We never managed to get 'smoothness' per bin, so just give up and smooth a lot
        bins = (1, 1)

    x_width = float(x_axis.value_range.max - x_axis.value_range.min) / bins[0] / 4
    y_width = float(y_axis.value_range.max - y_axis.value_range.min) / bins[1] / 4

    return (x_width, y_width)


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


def func_width_at_height(f: SmoothingFunc, height_fraction: float) -> tuple[FloatLike, FloatLike]:
    """Helper to calculate function width at a given fractional height."""
    if isinstance(f, SmoothingFuncWithWidth) and height_fraction in f.precalc_widths:
        return f.precalc_widths[height_fraction]
    x_width = func_span(partial_first(f), height_fraction)
    y_width = func_span(partial_second(f), height_fraction)
    if isinstance(f, SmoothingFuncWithWidth):
        f.precalc_widths[height_fraction] = (x_width, y_width)
    return x_width, y_width


def func_width_half_height(f: SmoothingFunc) -> tuple[FloatLike, FloatLike]:
    """Provide the (half) width of the function at half height (HWHM)"""
    return func_width_at_height(f, 0.5)


def func_width(f: SmoothingFunc) -> tuple[FloatLike, FloatLike]:
    """Provide the (half) width of the function where it becomes negligible

    Note: here we're just finding where the function gets down to 1/1000 of max,
    which neglects that the area scales with the radius from the function center,
    so for very slowly decaying functions (1/r, say) we may be excluding a lot of total weight.
    """
    return func_width_at_height(f, 0.001)


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
        round(kernel_width[0] / x_delta) + 1,
        round(kernel_width[1] / y_delta) + 1,
    )
    for point in points:
        p = (float(point[0]), float(point[1]))
        min_xi = max(round((p[0] - x_ctr_f[0]) / x_delta) - kernel_width_di[0], 0)
        min_yi = max(round((p[1] - y_ctr_f[0]) / y_delta) - kernel_width_di[1], 0)

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

    expanded_bins = expand_bins_arg(bins)

    if isinstance(expanded_bins[0], Sequence):
        # we were given the bin centers, so just use them
        padding: tuple[FloatLike, FloatLike] = (0, 0)
    else:
        # we're computing the bin centers, so include some padding based on kernel width
        padding = func_width_half_height(kernel)

    x_centers, y_centers = process_bin_args(points, expanded_bins, ranges, align, padding)
    x_axis = Axis((x_centers[0], x_centers[-1]), values_are_edges=False, **axis_args)
    y_axis = Axis((y_centers[0], y_centers[-1]), values_are_edges=False, **axis_args)

    return (smooth_to_bins(points, kernel, x_centers, y_centers), x_axis, y_axis)
