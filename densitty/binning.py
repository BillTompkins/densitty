"""Bin point data for a 2-D histogram"""

import math
from bisect import bisect_right
from decimal import Decimal
from fractions import Fraction
from typing import Optional, Sequence

from .axis import Axis
from .util import FloatLike, ValueRange
from .util import clamp, make_decimal, make_value_range, most_round, round_up_ish


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
        return make_value_range((0, 1))

    # bins are closed on left and open on right: i.e. left_edge <= values < right_edge
    # so, the right-most bin edge needs to be larger than the largest data value:
    max_value = max(values)
    min_value = min(values)
    data_value_range = make_value_range((min_value, max_value))
    range_top = data_value_range.max + Decimal(
        math.ulp(data_value_range.max)
    )  # increase by smallest representable amount
    return ValueRange(data_value_range.min, range_top)


def segment_interval(
    num_outputs: int,
    value_range: ValueRange,
    align=True,
) -> Sequence[FloatLike]:
    """Pick bin edges based on data values.

    Parameters
    ----------
    values: Sequence of data values
    num_outputs: int
              Number of output values
    value_range: ValueRange
              Min/Max of the output values
    align: bool
              Adjust the range somewhat to put bin size & edges on "round" values
    """
    value_range = make_value_range(value_range)  # coerce into Decimal if not already
    assert isinstance(value_range.min, Decimal)  # make the type-checker happy
    assert isinstance(value_range.max, Decimal)
    num_steps = num_outputs - 1

    min_step_size = (value_range.max - value_range.min) / num_steps
    if align:
        step_size = round_up_ish(min_step_size)
        first_edge = math.floor(Fraction(value_range.min) / step_size) * step_size
        if first_edge + num_steps * step_size < value_range.max:
            # Uh oh: even though we rounded up the bin size, shifting the first edge
            # down to a multiple has shifted the last edge down too far. Bump up the step size:
            step_size = round_up_ish(step_size * Fraction(65, 64))
            first_edge = math.floor(Fraction(value_range.min) / step_size) * step_size
        # we now have a round step size, and a first edge that the highest possible multiple of it
        # Test to see if any lower multiples of it will still include the whole ranges,
        # and be "nicer" i.e. if data is all in 1.1..9.5 range with 10 bins, we now have bins
        # covering 1-11, but could have 0-10
        last_edge = first_edge + step_size * num_steps
        edge_pairs = []
        max_step_slop = int((last_edge - Fraction(value_range.max)) // step_size)
        for step_shift in range(-max_step_slop, 1):
            for end_step_shift in range(-max_step_slop, step_shift + 1):
                edge_pairs += [
                    (first_edge + step_shift * step_size, last_edge + end_step_shift * step_size)
                ]
        first_edge, last_edge = most_round(edge_pairs)
    else:
        step_size = min_step_size
        first_edge = value_range.min
        last_edge = value_range.max

    stepped_values = tuple(first_edge + step_size * i for i in range(num_outputs))

    # The values may have overrun the end of the desired output range. Trim if so:
    return tuple(v for v in stepped_values if v <= last_edge)


def edge_range(start: Decimal, end: Decimal, step: Decimal, align: bool):
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
        x_range, y_range = make_value_range(ranges[0]), make_value_range(ranges[1])

    if not isinstance(bin_sizes, tuple):
        # given just a single bin size: replicate it for both axes:
        bin_sizes = (bin_sizes, bin_sizes)

    x_edges = tuple(edge_range(x_range.min, x_range.max, make_decimal(bin_sizes[0]), align))
    y_edges = tuple(edge_range(y_range.min, y_range.max, make_decimal(bin_sizes[1]), align))

    x_axis = Axis(x_range, values_are_edges=True, **axis_args)
    y_axis = Axis(y_range, values_are_edges=True, **axis_args)

    return (bin_edges(points, x_edges, y_edges, drop_outside=drop_outside), x_axis, y_axis)


def expand_bins_arg(
    bins: (
        int
        | tuple[int, int]
        | Sequence[FloatLike]
        | tuple[Sequence[FloatLike], Sequence[FloatLike]]
    ),
) -> tuple[int, int] | tuple[Sequence[FloatLike], Sequence[FloatLike]]:
    """Deal with 'bins' argument that is meant to apply to both axes"""
    if isinstance(bins, int):
        # we were given a single # of bins
        return (bins, bins)

    if len(bins) > 2:
        # we were given a single list of bin edges: replicate it
        return (bins, bins)

    # Flagged by type-checker: 'bins' could conceivably be a Sequence of len 1 or 2
    if not isinstance(bins, tuple):
        raise ValueError("Invalid 'bins' argument")

    # We got a tuple of int/int or of Sequence/Sequence: return it
    return bins


def bins_to_edges(
    bins: tuple[int, int] | tuple[Sequence[FloatLike], Sequence[FloatLike]],
) -> tuple[int, int] | tuple[Sequence[FloatLike], Sequence[FloatLike]]:
    """Number of edges = number of bins + 1. 'bins' argument may be # of bins,
    or a collection of edges. Only add 1 in the former case.
    """
    if isinstance(bins[0], int):
        return (bins[0] + 1, bins[1] + 1)
    return bins


def find_range(points: Sequence[FloatLike], padding: FloatLike) -> ValueRange:
    """Calculate a range if none is provided, then produce segment values"""

    range_unpadded = calc_value_range(points)
    range_padding = make_decimal(padding)
    return ValueRange(range_unpadded.min - range_padding, range_unpadded.max + range_padding)


def segment_one_dim_if_needed(
    points: Sequence[FloatLike],
    bins: int | Sequence[FloatLike],
    out_range: Optional[ValueRange],
    align: bool,
    padding: FloatLike,
) -> Sequence[FloatLike]:
    """Helper function for processing 'bins' argument:
    If 'bins' argument is a number of bins, find equally spaced values in the range.
    If not given a range, compute it first.
    """
    if isinstance(bins, int):
        # we were given the number of bins for X or Y. Calculate the edges/centers:
        if out_range is None:
            out_range = find_range(points, padding)
        return segment_interval(bins, out_range, align)

    # we were given the bin edges/centers already
    if out_range is not None:
        raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
    return bins


def process_bin_args(
    points: Sequence[tuple[FloatLike, FloatLike]],
    bins: tuple[int, int] | tuple[Sequence[FloatLike], Sequence[FloatLike]],
    ranges: Optional[tuple[Optional[ValueRange], Optional[ValueRange]]],
    align: bool,
    padding: tuple[FloatLike, FloatLike],
) -> tuple[Sequence[FloatLike], Sequence[FloatLike]]:
    """Utility function to process the various types that a 'bins' argument might be
    bins, ranges, align: as for histogram2d
    """

    if ranges is None:
        ranges = (None, None)

    x_edges = segment_one_dim_if_needed(
        tuple(x for x, _ in points), bins[0], ranges[0], align, padding[0]
    )
    y_edges = segment_one_dim_if_needed(
        tuple(y for _, y in points), bins[1], ranges[1], align, padding[1]
    )

    return x_edges, y_edges


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

    expanded_bins = bins_to_edges(expand_bins_arg(bins))

    x_edges, y_edges = process_bin_args(points, expanded_bins, ranges, align, (0, 0))

    x_axis = Axis((x_edges[0], x_edges[-1]), values_are_edges=True, **axis_args)
    y_axis = Axis((y_edges[0], y_edges[-1]), values_are_edges=True, **axis_args)

    return (bin_edges(points, x_edges, y_edges, drop_outside), x_axis, y_axis)
