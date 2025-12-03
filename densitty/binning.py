"""Bin point data for a 2-D histogram"""

from bisect import bisect_right
from decimal import Decimal
import math
from typing import Optional, Sequence
from .util import FloatLike, ValueRange
from .util import clamp, pick_step_size


def bin_edges(
    points: Sequence[tuple[FloatLike, FloatLike]],
    x_edges: Sequence[FloatLike],
    y_edges: Sequence[FloatLike],
    drop_outside: bool = True,
) -> Sequence[Sequence[int]]:
    """Bin points into a 2-D histogram

    Parameters
    ----------
    points:  Sequence of (X,Y) tuples: the points to bin
    x_edges: Sequence of values: Edges of the bins in X (N+1 values for N bins)
    y_edges: Sequence of values: Edges of the bins in Y (N+1 values for N bins)
    drop_outside: bool (default: True)
             True: Drop any data points outside the ranges
             False: Put any outside points in closest bin (i.e. edge bins include outliers)
    """
    num_x_bins = len(x_edges) - 1
    num_y_bins = len(y_edges) - 1
    out = [[0 for x in range(num_x_bins)] for y in range(num_y_bins)]
    for x, y in points:
        x_idx = bisect_right(x_edges, x) - 1
        y_idx = bisect_right(y_edges, y) - 1
        if drop_outside:
            if 0 <= x_idx < num_x_bins and 0 <= y_idx < num_y_bins:
                out[y_idx][x_idx] += 1
        else:
            out[clamp(y_idx, 0, num_y_bins - 1)][clamp(x_idx, 0, num_x_bins - 1)] += 1
    return out


def calc_value_range(values: Sequence[FloatLike]) -> ValueRange:
    """Calculate a value range from data values"""
    if not values:
        # Could raise an exception here, but for now just return _something_
        return ValueRange(0, 1)

    # bins are closed on left and open on right: i.e. left_edge <= values < right_edge
    # so, the right-most bin edge needs to be larger than the largest data value:
    max_value = max(values)
    range_top = max_value + math.ulp(max_value)  # increase by smallest representable amount
    return ValueRange(min(values), range_top)


def pick_edges(
    num_bins: int,
    value_range: ValueRange,
    auto_adjust_bins=True,
) -> Sequence[FloatLike]:
    """Pick bin edges based on data values.

    Parameters
    ----------
    values: Sequence of data values
    num_bins: int
              Number of bins to partition into
    value_range: Optional 2-tuple
              (min, max) to use for binning. Default: take from data.
    auto_adjust_bins: bool
              Adjust the bin number & range somewhat to put edges on "round" values
    """
    if auto_adjust_bins:
        step_size, _ = pick_step_size(value_range, num_bins)
        first_edge = math.floor(Decimal(value_range.min) / step_size) * step_size
        num_edges = math.ceil((Decimal(value_range.max) - first_edge) / step_size) + 1
    else:
        step_size = (value_range.max - value_range.min) / num_bins
        first_edge = value_range.min
        num_edges = num_bins + 1
    return tuple(first_edge + step_size * i for i in range(num_edges))


def bin_pick_num_bins(
    points: Sequence[tuple[FloatLike, FloatLike]],
    num_bins: tuple[int, int],
    ranges: Optional[tuple[ValueRange, ValueRange]] = None,
    auto_adjust_bins=True,
) -> tuple[Sequence[Sequence[int]], ValueRange, ValueRange]:
    """Bin points into a 2-D histogram

    Parameters
    ----------
    points: Sequence of (X,Y) tuples: the points to bin
    num_bins: Tuple(int, int)
                Number of (X,Y) bins to partition into
    ranges:  Optional ((float, float), (float, float))
                ((x_min, x_max), (y_min, y_max)) to use for binning. Default: take from data.
    auto_adjust_bins: bool
                Adjust the number/ranges somewhat to put bin edges on "round" values
    returns: Sequence[Sequence[int]], ValueRange(min_x, max_x), ValueRange(min_y, max_y)
    """

    if ranges is None:
        x_range = calc_value_range(tuple(x for x, _ in points))
        y_range = calc_value_range(tuple(y for _, y in points))
    else:
        x_range, y_range = ValueRange(*ranges[0]), ValueRange(*ranges[1])

    x_edges = pick_edges(num_bins[0], x_range, auto_adjust_bins)
    y_edges = pick_edges(num_bins[1], y_range, auto_adjust_bins)

    return (
        bin_edges(points, x_edges, y_edges),
        ValueRange(x_edges[0], x_edges[-1]),
        ValueRange(y_edges[0], y_edges[-1]),
    )


def edge_range(start: FloatLike, end: FloatLike, step: FloatLike, align: bool):
    """Similar to range/np.arange, but includes "end" in the output if appropriate"""
    if align:
        v = math.floor(start / step) * step
    else:
        v = start
    while v < end + step:
        if align:
            yield round(v / step) * step
        else:
            yield v
        v += step


# TODO: Should binning return Axes, so that the ticks make sense given the bins?
#       In that case, probably need to take Axes as input as well, instead of 'ranges'


def bin_data(
    points: Sequence[tuple[FloatLike, FloatLike]],
    bin_sizes: tuple[FloatLike, FloatLike],
    ranges: Optional[tuple[ValueRange, ValueRange]] = None,
    align_bins=True,
    drop_outside=True,
) -> tuple[Sequence[Sequence[int]], ValueRange, ValueRange]:
    """Bin points into a 2-D histogram

    Parameters
    ----------
    points: Sequence of (X,Y) tuples: the points to bin
    bin_sizes: Tuple(float, float)
                Sizes of (X,Y) bins to partition into
    ranges: Optional (ValueRange, ValueRange)
                ((x_min, x_max), (y_min, y_max)) for the bins. Default: take from data.
    align_bins: bool (default: True)
                Force bin edges to be at a multiple of the bin size
    drop_outside: bool (default: True)
                True: Drop any data points outside the ranges
                False: Put any outside points in closest bin (i.e. edge bins include outliers)
    returns: Sequence[Sequence[int]], ValueRange(min_x, max_x), ValueRange(min_y, max_y)
    """

    if ranges is None:
        x_range = calc_value_range(tuple(x for x, _ in points))
        y_range = calc_value_range(tuple(y for _, y in points))
    else:
        x_range, y_range = ValueRange(*ranges[0]), ValueRange(*ranges[1])

    x_edges = tuple(edge_range(x_range.min, x_range.max, bin_sizes[0], align_bins))
    y_edges = tuple(edge_range(y_range.min, y_range.max, bin_sizes[1], align_bins))

    return (
        bin_edges(points, x_edges, y_edges, drop_outside=drop_outside),
        ValueRange(x_edges[0], x_edges[-1]),
        ValueRange(y_edges[0], y_edges[-1]),
    )
