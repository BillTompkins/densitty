"""Bin point data for a 2-D histogram"""

import math
from bisect import bisect_right
from decimal import Decimal
from typing import Optional, Sequence

from .axis import Axis
from .util import FloatLike, ValueRange
from .util import clamp, decimal_value_range, most_round, round_up_ish


def bin_edges(
    points: Sequence[tuple[FloatLike, FloatLike]],
    x_edges: Sequence[FloatLike],
    y_edges: Sequence[FloatLike],
    drop_outside: bool = True,
) -> Sequence[Sequence[int]]:
    """Bin points into a 2-D histogram given bin edges

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
    align=True,
) -> Sequence[FloatLike]:
    """Pick bin edges based on data values.

    Parameters
    ----------
    values: Sequence of data values
    num_bins: int
              Number of bins to partition into
    value_range: ValueRange
              Min/Max of the values to be binned
    align: bool
              Adjust the range somewhat to put bin size & edges on "round" values
    """
    value_range = decimal_value_range(value_range)  # coerce into Decimal if not already

    min_step_size = (value_range.max - value_range.min) / num_bins
    if align:
        step_size = round_up_ish(min_step_size)
        first_edge = math.floor(Decimal(value_range.min) / step_size) * step_size
        if first_edge + num_bins * step_size < value_range.max:
            # Uh oh: even though we rounded up the bin size, shifting the first edge
            # down to a multiple has shifted the last edge down too far. Bump up the step size:
            step_size = round_up_ish(step_size * Decimal(1.015625))
            first_edge = math.floor(Decimal(value_range.min) / step_size) * step_size
        # we now have a round step size, and a first edge that the highest possible multiple of it
        # Test to see if any lower multiples of it will still include the whole ranges,
        # and be "nicer" i.e. if data is all in 1.1..9.5 range with 10 bins, we now have bins
        # covering 1-11, but could have 0-10
        last_edge = first_edge + step_size * num_bins
        num_trials = int((last_edge - value_range.max) // step_size + 1)
        offsets = (step_size * i for i in range(num_trials))
        edge_pairs = ((first_edge - offset, last_edge - offset) for offset in offsets)
        first_edge = most_round(edge_pairs)[0]

    else:
        step_size = min_step_size
        first_edge = value_range.min

    num_edges = num_bins + 1
    return tuple(first_edge + step_size * i for i in range(num_edges))


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


def bin_with_size(
    points: Sequence[tuple[FloatLike, FloatLike]],
    bin_sizes: FloatLike | tuple[FloatLike, FloatLike],
    ranges: Optional[tuple[ValueRange, ValueRange]] = None,
    align=True,
    drop_outside=True,
    **axis_args,
) -> tuple[Sequence[Sequence[int]], Axis, Axis]:
    """Bin points into a 2-D histogram, given bin sizes

    Parameters
    ----------
    points: Sequence of (X,Y) tuples: the points to bin
    bin_sizes: float or tuple(float, float)
                Size(s) of (X,Y) bins to partition into
    ranges: Optional (ValueRange, ValueRange)
                ((x_min, x_max), (y_min, y_max)) for the bins. Default: take from data.
    align: bool (default: True)
                Force bin edges to be at a multiple of the bin size
    drop_outside: bool (default: True)
                True: Drop any data points outside the ranges
                False: Put any outside points in closest bin (i.e. edge bins include outliers)
    axis_args: Extra arguments to pass through to Axis constructor

    returns: Sequence[Sequence[int]], (x-)Axis, (y-)Axis
    """

    if ranges is None:
        x_range = calc_value_range(tuple(x for x, _ in points))
        y_range = calc_value_range(tuple(y for _, y in points))
    else:
        x_range, y_range = ValueRange(*ranges[0]), ValueRange(*ranges[1])

    if not isinstance(bin_sizes, tuple):
        # given just a single bin size: replicate it for both axes:
        bin_sizes = (bin_sizes, bin_sizes)

    x_edges = tuple(edge_range(x_range.min, x_range.max, bin_sizes[0], align))
    y_edges = tuple(edge_range(y_range.min, y_range.max, bin_sizes[1], align))

    x_axis = Axis(x_range, values_are_edges=True, **axis_args)
    y_axis = Axis(y_range, values_are_edges=True, **axis_args)

    return (bin_edges(points, x_edges, y_edges, drop_outside=drop_outside), x_axis, y_axis)


def histogram2d(
    points: Sequence[tuple[FloatLike, FloatLike]],
    bins: (
        int
        | tuple[int, int]
        | Sequence[FloatLike]
        | tuple[Sequence[FloatLike], Sequence[FloatLike]]
    ) = 10,
    ranges: Optional[tuple[Optional[ValueRange], Optional[ValueRange]]] = None,
    align=True,
    drop_outside=True,
    **axis_args,
) -> tuple[Sequence[Sequence[int]], Axis, Axis]:
    """Bin points into a 2-D histogram, given number of bins, or bin edges

    Parameters
    ----------
    points: Sequence of (X,Y) tuples: the points to bin
    bins: int or (int, int) or [float,...] or ([float,...], [float,...])
                int: number of bins for both X & Y (default: 10)
                (int,int): number of bins in X, number of bins in Y
                list[float]: bin edges for both X & Y
                (list[float], list[float]): bin edges for X, bin edges for Y
    ranges: Optional (ValueRange, ValueRange)
                ((x_min, x_max), (y_min, y_max)) for the bins if # of bins is provided
                Default: take from data.
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
        else:
            x_range = ValueRange(*ranges[0])

        x_edges = pick_edges(bins[0], x_range, align)
    else:
        # we were given the bin edges already
        if ranges is not None and ranges[0] is not None:
            raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
        assert isinstance(bins[0], Sequence)
        x_edges = bins[0]

    if isinstance(bins[1], int):
        # we were given the number of bins. Calculate the edges:
        if ranges is None or ranges[1] is None:
            y_range = calc_value_range(tuple(y for _, y in points))
        else:
            y_range = ValueRange(*ranges[1])

        y_edges = pick_edges(bins[1], y_range, align)
    else:
        # we were given the bin edges already
        if ranges is not None and ranges[1] is not None:
            raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
        assert isinstance(bins[1], Sequence)
        y_edges = bins[1]

    x_axis = Axis((x_edges[0], x_edges[-1]), values_are_edges=True, **axis_args)
    y_axis = Axis((y_edges[0], y_edges[-1]), values_are_edges=True, **axis_args)

    return (bin_edges(points, x_edges, y_edges, drop_outside), x_axis, y_axis)
