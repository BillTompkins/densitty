"""Two-dimensional histogram (density plot) with textual output."""

import dataclasses
from itertools import chain, zip_longest
import os
import sys
from typing import Callable, Optional, Sequence

from . import ansi, axis, binning, lineart
from .util import FloatLike, ValueRange

# pylint: disable=invalid-name
# User can set this to provide a default if os.terminal_size() fails:
default_terminal_size: Optional[os.terminal_size] = None


@dataclasses.dataclass
class Plot:
    """Create a textual 2-D density/histogram plot given binned data."""

    # pylint: disable=too-many-instance-attributes
    data: Sequence[Sequence[FloatLike]]
    color_map: Callable = ansi.GRAYSCALE  # Can return an ascii character or a color code
    render_halfheight: bool = (
        True  # use fg/bg of "▄" to double Y resolution if color_map is non-ASCII
    )
    font_mapping: dict = dataclasses.field(default_factory=lambda: lineart.basic_font)
    min_data: Optional[FloatLike] = None
    max_data: Optional[FloatLike] = None
    x_axis: Optional[axis.Axis] = None
    y_axis: Optional[axis.Axis] = None
    flip_y: bool = True  # put the first row of data at the bottom of the output

    @classmethod
    def from_points(
        cls,
        points: Sequence[tuple[FloatLike, FloatLike]],
        num_bins: Optional[tuple[int, int]] = None,
        *,
        bin_sizes: Optional[tuple[FloatLike, FloatLike]] = None,
        ranges: Optional[tuple[ValueRange, ValueRange]] = None,
        auto_adjust_bins: bool = True,
        create_axes: bool = True,
        **kwargs,
    ):
        # pylint: disable=too-many-arguments
        """Create a Plot from raw point data by automatically binning it.

        This is a convenience method that combines binning and plot creation in one step.

        Parameters
        ----------
        points : Sequence[tuple[FloatLike, FloatLike]]
            Sequence of (X, Y) coordinate tuples to be plotted
        num_bins : Optional[tuple[int, int]]
            Number of (X, Y) bins to partition data into. If None, defaults to (80, 40).
            Mutually exclusive with bin_sizes.
        bin_sizes : Optional[tuple[FloatLike, FloatLike]] (keyword-only)
            Sizes of (X, Y) bins. If provided, overrides num_bins.
        ranges : Optional[tuple[ValueRange, ValueRange]] (keyword-only)
            ((x_min, x_max), (y_min, y_max)) for the bins. If None, computed from data.
        auto_adjust_bins : bool (keyword-only)
            If True, adjust bin edges to fall on "round" values. Default: True.
        create_axes : bool (keyword-only)
            If True, automatically create X and Y axes unless axes are explicitly
            provided in kwargs. Default: True.
        **kwargs
            Additional keyword arguments passed to Plot constructor (e.g., color_map,
            render_halfheight, min_data, max_data, flip_y, x_axis, y_axis).
            Note: If create_axes=True and x_axis/y_axis are not in kwargs, they will
            be automatically generated.

        Returns
        -------
        Plot
            A new Plot instance with binned data and optional axes.

        Examples
        --------
        >>> import random
        >>> points = [(random.random(), random.random()) for _ in range(1000)]
        >>> plot = Plot.from_points(points, num_bins=(50, 25))
        >>> plot.show()

        >>> # Or with specific bin sizes
        >>> plot = Plot.from_points(points, bin_sizes=(0.1, 0.1))
        >>> plot.show()
        """
        # Default to 80x40 bins if neither num_bins nor bin_sizes is specified
        # This provides reasonable resolution for most terminal sizes and can be
        # further scaled with the upscale() method if needed
        if num_bins is None and bin_sizes is None:
            num_bins = (80, 40)

        # Validate that only one of num_bins or bin_sizes is specified
        if num_bins is not None and bin_sizes is not None:
            raise ValueError("Cannot specify both num_bins and bin_sizes")

        # Bin the data using the appropriate method
        if bin_sizes is not None:
            binned_data, x_range, y_range = binning.bin_data(
                points,
                bin_sizes,
                ranges=ranges,
                align_bins=auto_adjust_bins,
            )
        else:
            binned_data, x_range, y_range = binning.bin_pick_num_bins(
                points,
                num_bins,
                ranges=ranges,
                auto_adjust_bins=auto_adjust_bins,
            )

        # Create axes if requested and not already provided
        # Note: If create_axes=True and axes are in kwargs, the user-provided axes take precedence
        if create_axes:
            if "x_axis" not in kwargs:
                kwargs["x_axis"] = axis.Axis(x_range, values_are_edges=True)
            if "y_axis" not in kwargs:
                kwargs["y_axis"] = axis.Axis(y_range, values_are_edges=True)

        # Create and return the Plot
        return cls(data=binned_data, **kwargs)

    def as_ascii(self):
        """Output using direct characters (ASCII-art)."""
        data = self._normalize_data()
        for line in data:
            line_str = (self.color_map(x, None) for x in line)
            yield "".join(line_str)

    def as_color(self):
        """Output using ANSI color codes for background, with space character."""
        data = self._normalize_data()
        for line in data:
            colors = (self.color_map(x, None) for x in line)
            yield (" ".join(chain(colors, [ansi.RESET])))

    def as_halfheight_color(self):
        """Output using ANSI color codes for foreground & background, with half-block character."""
        data = self._normalize_data()
        half_block = "▄"  # Unicode U+2584 "Lower Half Block"
        line_count = len(data)
        lines = iter(data)
        if line_count % 2:
            # odd number of lines: special-case the first line:
            line = next(lines, [])
            colors = (self.color_map(None, x) for x in line)
            yield (half_block.join(chain(colors, [ansi.RESET])))
        for bg_line in lines:
            fg_line = next(lines, [])
            colors = (self.color_map(x, y) for x, y in zip(bg_line, fg_line))
            yield (half_block.join(chain(colors, [ansi.RESET])))

    def _normalize_data(self):
        """Normalize data to 0..1 interval based on min_data/max_data or actual min/max.
        Also flips data if requested
        """

        min_data = min(min(line) for line in self.data) if self.min_data is None else self.min_data
        max_data = max(max(line) for line in self.data) if self.max_data is None else self.max_data
        data_scale = max_data - min_data
        if data_scale == 0:
            # all data has the same value (or we were told it does)
            data_scale = sys.float_info.min
        norm_data = tuple(tuple((x - min_data) / data_scale for x in line) for line in self.data)

        return tuple(reversed(norm_data)) if self.flip_y else norm_data

    def is_color(self):
        """Is color_map returning color codes, not ASCII-art?"""
        return len(self.color_map(0.5, None)) > 1  # is color_map returning color codes?

    def is_halfheight(self):
        """Are there two pixels per output character?"""
        return self.is_color() and self.render_halfheight

    def as_strings(self):
        """Scale data to 0..1 range and feed it through the appropriate output function"""
        if self.is_halfheight():
            plot_lines = tuple(self.as_halfheight_color())
        elif self.is_color():
            plot_lines = tuple(self.as_color())
        else:
            plot_lines = tuple(self.as_ascii())

        num_rows = len(plot_lines)
        num_cols = len(self.data[0])

        if self.y_axis:
            axis_lines = self.y_axis.render_as_y(num_rows, False, bool(self.x_axis), self.flip_y)
        else:
            axis_lines = ["" for _ in range(num_rows + bool(self.x_axis))]

        left_margin = lineart.display_len(axis_lines[0])
        if self.x_axis:
            x_ticks, x_labels = self.x_axis.render_as_x(num_cols, left_margin)
            axis_lines[-1] = lineart.merge_lines(x_ticks, axis_lines[-1])
            axis_lines += [x_labels]

        for frame, plot_line in zip_longest(axis_lines, plot_lines, fillvalue=""):
            yield frame.translate(self.font_mapping) + plot_line

    def show(self, printer=print):
        """Simple helper function to output/print a plot"""
        for line in self.as_strings():
            printer(line)

    def _compute_scaling_multipliers(
        self,
        max_size: tuple[int, int],
        keep_aspect_ratio: bool,
    ) -> tuple[float, float]:
        """Compute multpliers in X and Y (cols/rows) to resize data to fit in specified bounds."""
        try:
            terminal_size: Optional[os.terminal_size] = os.get_terminal_size()
        except OSError:
            terminal_size = default_terminal_size

        if max_size[1] <= 0:
            if terminal_size is None:
                raise OSError("No terminal size from os.get_terminal_size()")
            user_margin = -int(max_size[1]) if max_size[1] else 0
            axis_margin = bool(self.x_axis) * 2  # 2 lines at bottom for X axis
            y_mult = 2 if self.is_halfheight() else 1
            max_size = (max_size[0], (terminal_size.lines - user_margin - axis_margin) * y_mult)

        if max_size[0] <= 0:
            if terminal_size is None:
                raise OSError("No terminal size from os.get_terminal_size()")
            user_margin = -int(max_size[0]) if max_size[0] else 0
            if self.y_axis:
                y_axis_lines = self.y_axis.render_as_y(
                    max_size[1], False, bool(self.x_axis), self.flip_y
                )
                # margin on left from Y axis width. 2-char buffer on right for X axis label:
                axis_margin = len(y_axis_lines[0]) + 2 * bool(self.x_axis)
            else:
                axis_margin = 0
            max_size = (terminal_size.columns - user_margin - axis_margin, max_size[1])

        scaling = (max_size[0] / len(self.data[0]), max_size[1] / len(self.data))
        if keep_aspect_ratio:
            single_scale = min(scaling)
            return single_scale, single_scale
        return scaling

    def upscale(
        self,
        max_size: tuple[int, int] = (0, 0),
        max_expansion: tuple[int, int] = (3, 3),
        keep_aspect_ratio: bool = False,
    ):
        """Scale up 'data' by repeating lines and values within lines.

        Parameters
        ----------
        max_size : tuple (int, int)
                   If positive: Maximum number of columns, maximum number of rows
                   If zero: Use terminal size
                   If negative: Use as offset from terminal size
                   Default: Based on terminal size (0).
        max_expansion : tuple (int, int)
                   maximum expansion factor in each direction. Default (3,3). 0=> No maximum
        keep_aspect_ratio : bool
                   Require that X and Y scaling are equal.
        """

        float_mult = self._compute_scaling_multipliers(max_size, keep_aspect_ratio)
        col_mult = max(int(float_mult[0]), 1)
        row_mult = max(int(float_mult[1]), 1)

        if keep_aspect_ratio and any(max_expansion):
            # Just in case user specifies keep_aspect_ratio but varying / missing maxima:
            mult = max(int(m) for m in max_expansion)
            max_expansion = (mult, mult)

        if max_expansion[0] is not None:
            col_mult = min(col_mult, max_expansion[0])
        if max_expansion[1] is not None:
            row_mult = min(row_mult, max_expansion[1])

        def repeat_each(d, mult):
            """Repeat each element of 'd' 'mult' times"""
            return sum(((x,) * mult for x in d), start=tuple())

        # expand each of the lines using the column multiplier
        x_expanded = (repeat_each(data_line, col_mult) for data_line in self.data)

        # repeat each of those by the row multiplier
        self.data = repeat_each(x_expanded, row_mult)
        return self
