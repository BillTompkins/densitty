"""Bin point data for a 2-D histogram"""

import math
from bisect import bisect_right
from decimal import Decimal
from fractions import Fraction
from typing import Optional, Sequence

from .axis import Axis
from .util import FloatLike, ValueRange
from .util import clamp, make_decimal, make_value_range, most_round, round_up_ish

# Following MatPlotLib, the 'bins' argument for functions can be:
#  int:                                             number of bins for both X and Y
#  Sequence[FloatLike]:                             bin edges for both X and Y
#  tuple(int, int):                                 number of bins for X, number of bins for Y
#  tuple(Sequence[FloatLike], Sequence[FloatLike]): bin edges for X, bin edges for Y

CountArg = int
EdgesArg = Sequence[FloatLike]
# a type for the "for both X and Y" variants:
SingleBinsArg = CountArg | EdgesArg

# a type for the tuple (X,Y) variants:
DoubleCountArg = tuple[CountArg, CountArg]
DoubleEdgesArg = tuple[EdgesArg, EdgesArg]
ExpandedBinsArg = DoubleCountArg | DoubleEdgesArg

FullBinsArg = Optional[SingleBinsArg | ExpandedBinsArg]

RangesArg = tuple[Optional[ValueRange], Optional[ValueRange]]

DEFAULT_NUM_BINS = (10, 10)


def bin_by_edges(
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
    min_value = make_decimal(min(values))
    max_value = make_decimal(max(values))

    range_top = max_value + Decimal(
        math.ulp(max_value)
    )  # increase by smallest float-representable amount
    return ValueRange(min_value, range_top)


def align_value_range(vr: ValueRange, alignment_arg: FloatLike) -> ValueRange:
    """Shift the provided ValueRange up or down to the specified alignment.
    up/down choice based on which will shift it less"""
    alignment = make_decimal(alignment_arg)
    width = vr.max - vr.min
    aligned_min = math.floor(vr.min / alignment) * alignment
    aligned_max = math.ceil(vr.max / alignment) * alignment
    shift_for_min = vr.min - aligned_min  # how far down did 'min' get shifted?
    shift_for_max = aligned_max - vr.max  # how far up did 'max' get shifted?
    if shift_for_min < shift_for_max:
        return ValueRange(aligned_min, aligned_min + width)
    return ValueRange(aligned_max - width, aligned_max)


def force_value_range_width(vr: ValueRange, width: FloatLike) -> ValueRange:
    """Return a ValueRange with specified width, centered on an existing ValueRange"""
    half_width = make_decimal(width) / 2
    midpoint = (vr.max + vr.min) / 2
    return ValueRange(midpoint - half_width, midpoint + half_width)


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


def edge_range(rng: ValueRange, step_arg: FloatLike, align: bool):
    """Generator providing values containing range, by step.
    The first value will be rng.min, or rng.min rounded down to nearest 'step'
    The last value will be equal to or larger than rng.max"""

    step = make_decimal(step_arg)  # turn into decimal if it isn't already
    if align:
        v = math.floor(rng.min / step) * step
    else:
        v = rng.min

    while v < (rng.max + step).next_minus():
        if align:
            yield round(v / step) * step
        else:
            yield v
        v += step


def make_edges(rng: ValueRange, step_arg: FloatLike, align: bool):
    """Return the edges as from 'edge_range', as a tuple for convenience"""
    return tuple(edge_range(rng, step_arg, align))


def expand_bins_arg(
    bins: FullBinsArg,
) -> tuple[bool, DoubleCountArg, Optional[DoubleEdgesArg]]:
    """Deal with 'bins' that may be
    - None
    - an integer indicating number of bins
    - a list of edges/centers for the bins
    - a 2-tuple of either of those
    Returns a 3-tuple:
      - specified/not-default (bool),
      - 2-tuple of number of bins,
      - optional 2-tuple of lists of edges/centers
    """
    if bins is None:
        return (False, DEFAULT_NUM_BINS, None)
    if isinstance(bins, int):
        num_bins = (bins, bins)
        bin_positions = None
    elif len(bins) > 2:
        # we were given a single list of bin edges
        num = len(bins) - 1
        num_bins = (num, num)
        bin_positions = (bins, bins)
    else:
        if not isinstance(bins, tuple):
            raise ValueError("Invalid 'bins' argument")
        # we either have a tuple of int/int or Sequence/Sequence
        if isinstance(bins[0], int):
            num_bins = bins
            bin_positions = None
        else:
            num_bins = (len(bins[0]) - 1, len(bins[1]) - 1)
            bin_positions = bins
    return True, num_bins, bin_positions


def expand_bin_size_arg(
    bin_size: Optional[FloatLike | tuple[FloatLike, FloatLike]],
) -> Optional[tuple[FloatLike, FloatLike]]:
    """If bin_size arg is not a 2-tuple, replicate it into one"""
    if bin_size is None:
        return None
    if isinstance(bin_size, tuple):
        return bin_size
    return (bin_size, bin_size)


def range_from_arg_or_data(range_arg, points):
    """Return range arg if given, or calculate a range from the data"""
    if range_arg:
        return make_value_range(range_arg)
    return calc_value_range(tuple(points))


def histogram2d(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    points: Sequence[tuple[FloatLike, FloatLike]],
    bins: FullBinsArg = None,
    ranges: Optional[RangesArg] = None,
    bin_size: Optional[FloatLike | tuple[FloatLike, FloatLike]] = None,
    align=True,
    drop_outside=True,
    **axis_args,
) -> tuple[Sequence[Sequence[int]], Axis, Axis]:
    """Bin points into a 2-D histogram, given number of bins, bin edges, or bin sizes

    Parameters can be combined in the following ways:
    - bin_size with optional ranges
    - bins (as edges) with no ranges
    - bins (as count) with optional ranges
    - bins (as count) + bin_size with no ranges: Fixed number and size of bins, centered on data

    Parameters
    ----------
    points: Sequence of (X,Y) tuples: the points to bin
    bins: int or (int, int) or [float,...] or ([float,...], [float,...]) or None
                int: number of bins for both X & Y
                (int,int): number of bins in X, number of bins in Y
                list[float]: bin edges for both X & Y
                (list[float], list[float]): bin edges for X, bin edges for Y
                None: defaults to DEFAULT_NUM_BINS if bin_size is not provided
    ranges: Optional (ValueRange, ValueRange)
                ((x_min, x_max), (y_min, y_max)) for the bins if # of bins is provided
                Cannot be specified with bins (as count) + bin_size, or bins (as edges)
                Default if allowed: take from data
    bin_size: Optional float or (float, float)
                Size(s) of (X,Y) bins to partition into.
                Cannot be combined with bins (as edges) since edge spacing already determines size.
                float: bin size for both X & Y
                (float, float): bin size for X, bin size for Y
    align: bool (default: True)
                pick bin edges at 'round' values if # of bins is provided, or force bin edges
                to be at multiples of bin_size if bin_size is provided
    drop_outside: bool (default: True)
                True: Drop any data points outside the ranges
                False: Put any outside points in closest bin (i.e. edge bins include outliers)
    axis_args: Extra arguments to pass through to Axis constructor

    returns: Sequence[Sequence[int]], (x-)Axis, (y-)Axis
    """

    bins_specified, num_bins, bin_edges = expand_bins_arg(bins)

    bin_sizes = expand_bin_size_arg(bin_size)
    if ranges is None:
        ranges = (None, None)

    if bin_edges and any(ranges):
        raise ValueError("Cannot specify both bin edges and plot range")
    if bins_specified and bin_sizes and any(ranges):
        # The number of bins and bin size imply a size of plot range, so this
        # is overconstrained.
        raise ValueError("Cannot specify number of bins and bin size and plot range")

    x_range = range_from_arg_or_data(ranges[0], (x for x, _ in points))
    y_range = range_from_arg_or_data(ranges[1], (y for _, y in points))

    if bins_specified and bin_sizes:
        # range width must be num_bins * bin_sizes, so take the data's range
        # and force the width, aligning as needed
        x_range = force_value_range_width(x_range, num_bins[0] * bin_sizes[0])
        if align:
            x_range = align_value_range(x_range, bin_sizes[0])

        y_range = force_value_range_width(y_range, num_bins[1] * bin_sizes[1])
        if align:
            y_range = align_value_range(y_range, bin_sizes[1])

    # Handle different parameter combinations
    if bin_edges:
        x_edges, y_edges = bin_edges
    else:
        if bin_sizes:
            x_edges = make_edges(x_range, bin_sizes[0], align)
            y_edges = make_edges(y_range, bin_sizes[1], align)
        else:
            # Only number of bins provided, if that
            x_edges = segment_interval(num_bins[0] + 1, x_range, align)
            y_edges = segment_interval(num_bins[1] + 1, y_range, align)

    x_axis = Axis((x_edges[0], x_edges[-1]), values_are_edges=True, **axis_args)
    y_axis = Axis((y_edges[0], y_edges[-1]), values_are_edges=True, **axis_args)
    return (bin_by_edges(points, x_edges, y_edges, drop_outside), x_axis, y_axis)
