"""Kernel-based plot data generation."""

from __future__ import annotations

from typing import Callable, Optional, Sequence

from .axis import Axis
from .binning import calc_value_range, pick_edges
from .util import FloatLike, ValueRange

KernelFunc = Callable[[float, float], float]


def kernel_edges(
    points: Sequence[tuple[FloatLike, FloatLike]],
    x_edges: Sequence[FloatLike],
    y_edges: Sequence[FloatLike],
    kernel: KernelFunc,
    drop_outside: bool = True,
) -> Sequence[Sequence[float]]:
    """Apply a smoothing kernel across a 2-D grid defined by bin edges.

    Parameters
    ----------
    points: Sequence of (X,Y) tuples: the points to smooth
    x_edges: Sequence of values: Edges of the bins in X (N+1 values for N bins)
    y_edges: Sequence of values: Edges of the bins in Y (N+1 values for N bins)
    kernel: Callable taking (dx, dy) and returning a weight
    drop_outside: bool (default: True)
             True: Drop any data points outside the ranges
             False: Include all points regardless of position
    """
    if kernel is None:
        raise ValueError("kernel function must be provided")

    num_x_bins = len(x_edges) - 1
    num_y_bins = len(y_edges) - 1
    x_edges_f = tuple(float(v) for v in x_edges)
    y_edges_f = tuple(float(v) for v in y_edges)

    x_centers = tuple((x_edges_f[i] + x_edges_f[i + 1]) / 2 for i in range(num_x_bins))
    y_centers = tuple((y_edges_f[i] + y_edges_f[i + 1]) / 2 for i in range(num_y_bins))

    out = [[0.0 for _ in range(num_x_bins)] for _ in range(num_y_bins)]
    for x, y in points:
        x_val = float(x)
        y_val = float(y)
        if drop_outside and (
            x_val < x_edges_f[0]
            or x_val >= x_edges_f[-1]
            or y_val < y_edges_f[0]
            or y_val >= y_edges_f[-1]
        ):
            continue
        for y_idx, y_ctr in enumerate(y_centers):
            dy = y_val - y_ctr
            for x_idx, x_ctr in enumerate(x_centers):
                dx = x_val - x_ctr
                out[y_idx][x_idx] += kernel(dx, dy)
    return out


def _resolve_edges_and_axes(
    points: Sequence[tuple[FloatLike, FloatLike]],
    bins: (
        int
        | tuple[int, int]
        | Sequence[FloatLike]
        | tuple[Sequence[FloatLike], Sequence[FloatLike]]
    ),
    ranges: Optional[tuple[Optional[ValueRange], Optional[ValueRange]]],
    align: bool,
    axis_args: dict,
) -> tuple[Sequence[FloatLike], Sequence[FloatLike], Axis, Axis]:
    if isinstance(bins, int):
        bins = (bins, bins)

    if isinstance(bins, Sequence) and len(bins) > 2:
        bins = (bins, bins)

    if isinstance(bins[0], int):
        if ranges is None or ranges[0] is None:
            x_range = calc_value_range(tuple(x for x, _ in points))
        else:
            x_range = ranges[0]

        x_edges = pick_edges(bins[0], x_range, align)
    else:
        if ranges is not None and ranges[0] is not None:
            raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
        assert isinstance(bins[0], Sequence)
        x_edges = bins[0]

    if isinstance(bins[1], int):
        if ranges is None or ranges[1] is None:
            y_range = calc_value_range(tuple(y for _, y in points))
        else:
            y_range = ranges[1]

        y_edges = pick_edges(bins[1], y_range, align)
    else:
        if ranges is not None and ranges[1] is not None:
            raise ValueError("Both bin edges and bin ranges provided, pick one or the other")
        assert isinstance(bins[1], Sequence)
        y_edges = bins[1]

    x_axis = Axis((x_edges[0], x_edges[-1]), values_are_edges=True, **axis_args)
    y_axis = Axis((y_edges[0], y_edges[-1]), values_are_edges=True, **axis_args)
    return x_edges, y_edges, x_axis, y_axis


def kernel2d(
    points: Sequence[tuple[FloatLike, FloatLike]],
    bins: (
        int
        | tuple[int, int]
        | Sequence[FloatLike]
        | tuple[Sequence[FloatLike], Sequence[FloatLike]]
    ) = 10,
    kernel: Optional[KernelFunc] = None,
    ranges: Optional[tuple[Optional[ValueRange], Optional[ValueRange]]] = None,
    align: bool = True,
    drop_outside: bool = True,
    **axis_args,
) -> tuple[Sequence[Sequence[float]], Axis, Axis]:
    """Generate smoothed plot data from point input using a kernel function.

    Parameters
    ----------
    points: Sequence of (X,Y) tuples: the points to smooth
    bins: int or (int, int) or [float,...] or ([float,...], [float,...])
                int: number of bins for both X & Y (default: 10)
                (int,int): number of bins in X, number of bins in Y
                list[float]: bin edges for both X & Y
                (list[float], list[float]): bin edges for X, bin edges for Y
    kernel: Callable taking (dx, dy) and returning a weight
    ranges: Optional (ValueRange, ValueRange)
                ((x_min, x_max), (y_min, y_max)) for the bins if # of bins is provided
                Default: take from data.
    align: bool (default: True)
                pick bin edges at 'round' values if # of bins is provided
    drop_outside: bool (default: True)
                True: Drop any data points outside the ranges
                False: Include all points regardless of position
    axis_args: Extra arguments to pass through to Axis constructor

    returns: Sequence[Sequence[float]], (x-)Axis, (y-)Axis
    """
    if kernel is None:
        raise ValueError("kernel function must be provided")

    x_edges, y_edges, x_axis, y_axis = _resolve_edges_and_axes(
        points, bins, ranges, align, axis_args
    )
    smoothed = kernel_edges(points, x_edges, y_edges, kernel, drop_outside)
    return smoothed, x_axis, y_axis
