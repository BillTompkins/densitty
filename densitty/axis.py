"""Axis-generation support."""

import dataclasses
from decimal import Decimal
import itertools
import math
from typing import Optional

from . import lineart
from .util import FloatLike, ValueRange, pick_step_size

MIN_X_TICKS_PER_LABEL = 4
MIN_Y_TICKS_PER_LABEL = 2
DEFAULT_X_COLS_PER_TICK = 4
DEFAULT_Y_ROWS_PER_TICK = 2


@dataclasses.dataclass
class BorderChars:
    """Characters to use for X/Y border"""

    first: str
    middle: str
    last: str


y_border = {False: BorderChars(" ", " ", " "), True: BorderChars("╷", "│", "╵")}
x_border = {False: BorderChars(" ", " ", " "), True: BorderChars("╶", "─", "╴")}

###############################################
# Helper functions used by the Axis class below


def add_label(line: list[str], label: str, ctr_pos: int):
    """Adds the label string to the output line, centered at specified position
    The output line is a list of single-character strings, to make this kind of thing
    straightforward"""
    width = len(label)
    start_col = max(ctr_pos - width // 2, 0)
    end_col = start_col + width
    line[start_col:end_col] = list(label)


def gen_tick_values(value_range, tick_step):
    """Produce tick values in the specified range. Basically numpy.arange"""

    tick = math.ceil(value_range.min / tick_step) * tick_step
    while tick <= value_range.max:
        yield tick
        tick += tick_step


def gen_labels(
    value_range: ValueRange, num_ticks, min_ticks_per_label, fmt, label_end_ticks=False
):
    """Generate positions for labels (plain ticks & ticks with value)"""
    tick_step, label_step = pick_step_size(value_range, num_ticks, min_ticks_per_label)

    ticks = list(gen_tick_values(value_range, tick_step))
    label_values = list(gen_tick_values(value_range, label_step))
    if label_end_ticks or len(label_values) <= 2:
        # ensure that first & last ticks have labels:
        if label_values[0] != ticks[0]:
            label_values = ticks[:1] + label_values
        if label_values[-1] != ticks[-1]:
            label_values += ticks[-1:]

    # sanity: if all but one ticks have labels, just label them all
    if len(label_values) >= len(ticks) - 1:
        label_values = ticks

    ticks_only = {value: "" for value in ticks}
    labeled_ticks = {value: fmt.format(value) for value in label_values}

    return ticks_only | labeled_ticks


def calc_edges(value_range, num_bins, values_are_edges):
    """Calculate the top/bottom or left/right values for each of 'num_bins' bins

    Parameters
    ----------
    value_range: util.ValueRange
                 Coordinate values for first/last bin
                 Can be center of bin, or outside edge (see values_are_edges)
    num_bins:    int
                 Number of bins/intervals to produce edges for
    values_are_edges: bool
                 Indicates that value_range specifies outside edges rather than bin centers
    """
    if values_are_edges:
        bin_delta = (value_range.max - value_range.min) / num_bins
        first_bin_min = value_range.min
    else:
        bin_delta = (value_range.max - value_range.min) / (num_bins - 1)
        first_bin_min = value_range.min - (bin_delta / 2)
    bin_edges = tuple(first_bin_min + i * bin_delta for i in range(num_bins + 1))
    return itertools.pairwise(bin_edges)


###############################################
# The User-facing interface: the Axis class


@dataclasses.dataclass
class Axis:
    """Options for axis generation."""

    value_range: ValueRange  # can also specify as a tuple of (min, max)
    labels: Optional[dict[float, str]] = None  # map axis value to label (plus tick) at that value
    label_fmt: str = "{}"  # format for generated labels
    border_line: bool = False  # embed ticks in a horizontal X-axis or vertical Y-axis line
    values_are_edges: bool = False  # N+1 values, indicating boundaries between pixels, not centers
    fractional_tick_pos: bool = False  # Use "▔", "▁", or "╱╲" for non-centered ticks

    def __init__(
        self,
        value_range: ValueRange | tuple[FloatLike, FloatLike],
        labels: Optional[dict[float, str]] = None,
        label_fmt: str = "{}",
        border_line: bool = False,
        values_are_edges: bool = False,
        fractional_tick_pos: bool = False,
        # pylint: disable=too-many-arguments,too-many-positional-arguments
    ):
        # Sanitize value_range: allow user to provide it as a tuple of FloatLike (without
        # needing to import ValueRange), and convert to ValueRange(Decimal, Decimal)
        self.value_range = ValueRange(
            Decimal(float(value_range[0])), Decimal(float(value_range[1]))
        )
        self.labels = labels
        self.label_fmt = label_fmt
        self.border_line = border_line
        self.values_are_edges = values_are_edges
        self.fractional_tick_pos = fractional_tick_pos

    def _unjustified_y_axis(self, num_rows: int):
        """Returns the Y axis string for each line of the plot"""
        if self.labels is None:
            labels = gen_labels(
                self.value_range,
                num_rows // DEFAULT_Y_ROWS_PER_TICK,
                MIN_Y_TICKS_PER_LABEL,
                self.label_fmt,
            )
        else:
            labels = self.labels

        label_values = sorted(labels.keys())
        bins = calc_edges(self.value_range, num_rows, self.values_are_edges)

        use_combining = self.border_line and self.fractional_tick_pos
        for row_min, row_max in bins:
            if label_values and row_min <= label_values[0] <= row_max:
                label_str = labels[label_values[0]]

                offset_frac = (label_values[0] - row_min) / (row_max - row_min)
                if offset_frac < 0.25 and self.fractional_tick_pos:
                    tick_char = "▔"
                elif offset_frac > 0.75 and self.fractional_tick_pos:
                    tick_char = "▁"
                else:
                    tick_char = "─"
                label_str += lineart.merge_chars(
                    tick_char,
                    y_border[self.border_line].middle,
                    use_combining_unicode=use_combining,
                )
                yield label_str
                label_values = label_values[1:]
            else:
                yield y_border[self.border_line].middle

    def render_as_y(self, num_rows: int, pad_top: bool, pad_bot: bool, flip: bool):
        """Create a Y axis as a list of strings for the left margin of a plot

        Parameters
        ----------
        num_rows: int
                  Number of data rows
        pad_top:  bool
                  Emit a line for an X axis line/row at the top
        pad_bot:  bool
                  Emit a line for an X axis line/row at the bottom
        flip:     bool
                  Put the minimum Y on the last line rather than the first
        """
        unpadded_labels = list(self._unjustified_y_axis(num_rows))
        if flip:
            unpadded_labels = [
                s.translate(lineart.flip_vertical) for s in reversed(unpadded_labels)
            ]

        if pad_top:
            unpadded_labels = [y_border[self.border_line].first] + unpadded_labels
        if pad_bot:
            unpadded_labels = unpadded_labels + [y_border[self.border_line].last]

        lengths = [lineart.display_len(label_str) for label_str in unpadded_labels]
        max_width = max(lengths)
        pad_lengths = [max_width - length for length in lengths]
        padded_labels = [
            " " * pad_length + label_str
            for (label_str, pad_length) in zip(unpadded_labels, pad_lengths)
        ]
        return padded_labels

    def render_as_x(self, num_cols: int, left_margin: int):
        """Generate X tick line and X label line.

        Parameters
        ----------
        num_cols:    int
                     Number of data columns
        left_margin: int
                     chars to the left of leftmost data col. May have Labels/border-line.
        """

        if self.labels is None:
            labels = gen_labels(
                self.value_range,
                num_cols // DEFAULT_X_COLS_PER_TICK,
                MIN_X_TICKS_PER_LABEL,
                self.label_fmt,
            )
        else:
            labels = self.labels

        label_values = sorted(labels.keys())

        bins = calc_edges(self.value_range, num_cols, self.values_are_edges)

        tick_line = list(
            " " * (left_margin - 1)
            + x_border[self.border_line].first
            + x_border[self.border_line].middle * num_cols
            + x_border[self.border_line].last
        )

        label_line = [" "] * len(tick_line)  # labels under the ticks

        for col_idx, (col_min, col_max) in enumerate(bins):
            # use Decimal.next_plus to accomodate rounding error/truncation
            if label_values and col_min <= label_values[0] <= col_max.next_plus():
                add_label(label_line, labels[label_values[0]], col_idx + left_margin)
                tick_idx = left_margin + col_idx
                offset_frac = (label_values[0] - col_min) / (col_max - col_min)
                if self.fractional_tick_pos and offset_frac < 0.25:
                    if col_idx == 0:
                        tick_line[tick_idx - 1] = lineart.merge_chars("│", tick_line[tick_idx - 1])
                    else:
                        tick_line[tick_idx - 1] = "╱"
                    tick_line[tick_idx] = "╲"
                elif self.fractional_tick_pos and offset_frac > 0.75:
                    tick_line[tick_idx] = "╱"
                    if col_idx < num_cols - 1:
                        tick_line[tick_idx + 1] = "╲"
                    else:
                        tick_line[tick_idx + 1] = lineart.merge_chars("│", tick_line[tick_idx + 1])
                else:
                    tick_line[tick_idx] = lineart.merge_chars("│", tick_line[tick_idx])

                label_values = label_values[1:]  # pop that first label since we added it

        return "".join(tick_line), "".join(label_line)
