"""Axis-generation support."""

import dataclasses
from decimal import Decimal
import itertools
import math
from typing import Optional, Sequence

from . import lineart, util
from .util import FloatLike, ValueRange


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


def pick_step_size(lower_bound) -> Decimal:
    """Try to pick a step size that gives nice round values for step positions."""
    if lower_bound <= 0:
        raise ValueError("pick_step_size called with 0 or negative value")

    _, frac, exp = util.sfrexp10(lower_bound)  # 0.1 <= frac < 1.0

    # round up to an appropriate "round" value that starts with 1/2/5
    if frac <= Decimal("0.2"):
        out = Decimal((0, (2,), exp - 1))
    elif frac <= Decimal("0.5"):
        out = Decimal((0, (5,), exp - 1))
    else:
        out = Decimal((0, (1,), exp))

    if out >= 10:
        # this will be printed as 1E1 or such. Give it more significant figures so
        # it is printed as an integer:
        return out.quantize(1)
    return out


def add_x_label(line: list[str], label: str, ctr_pos: FloatLike):
    """Adds the label string to the output line, centered at specified position
    The output line is a list of single-character strings, to make this kind of thing
    straightforward"""
    width = len(label)
    start_col = int(max(float(ctr_pos) + 0.49 - width / 2, 0))
    end_col = start_col + width
    line[start_col:end_col] = list(label)


def add_x_tick(line: list[str], start_pos: float, left_margin: int, num_cols: int):
    """Adds a (possibly fractional) tick to the output line, centered at specified position"""
    base_idx = int(start_pos)
    fractional_pos = start_pos - base_idx
    margined_idx = base_idx + left_margin
    if 0.25 <= fractional_pos <= 0.75:
        # add a tick in the center of the appropriate bin
        line[margined_idx] = lineart.merge_chars("│", line[margined_idx])
        return
    if fractional_pos < 0.25:
        left_idx = max(margined_idx - 1, 0)
    else:
        left_idx = margined_idx

    if base_idx == 0:
        line[left_idx] = lineart.merge_chars("│", line[left_idx])
    else:
        line[left_idx] = "╱"

    if base_idx >= num_cols - 1:
        line[left_idx + 1] = lineart.merge_chars("│", line[left_idx + 1])
    else:
        line[left_idx + 1] = "╲"


def gen_tick_values(value_range, tick_step):
    """Produce tick values in the specified range. Basically numpy.arange"""

    tick = math.ceil(value_range.min / tick_step) * tick_step
    while tick <= value_range.max:
        yield tick
        tick += tick_step


def positions_to_labels(
    printed_positions: Sequence[Decimal], ticked_positions: Sequence[FloatLike], fmt: str
) -> dict[FloatLike, str]:
    """Given positions, construct a label dict mapping position to string to be printed there.
    The first positions get a printed value, the second set get a blank, for a bare 'tick'"""

    tick_dict = {p: "" for p in ticked_positions}
    printed_dict = {p: fmt.format(p) for p in util.sanitize_decimals(printed_positions)}
    return tick_dict | printed_dict


def calc_min_step(
    value_range: ValueRange,
    bin_width: FloatLike,
    accomodate_values: bool,
    tick_space: int,
    fmt: str,
):
    """Calculate minimum step size for tick placement.

    When accomodate_values is True, considers the width of printed labels.
    Otherwise, only considers tick spacing requirements.
    """
    if accomodate_values:
        # find a representative printed label width to use for basic calculations
        test_tick_step = pick_step_size((value_range.max - value_range.min) / 5)
        test_values_printed = tuple(
            fmt.format(value) for value in gen_tick_values(value_range, test_tick_step)
        )
        widths_in_bins = tuple(len(p) for p in test_values_printed)
        # get the 3'd lowest width, or highest if there are less than 3 due to tick-step roundup:
        example_width = sorted(widths_in_bins)[:3][-1]
        min_printed_step = (example_width + 1) * bin_width
        # If the printed labels are small (single-digit), the ticks themselves might be the
        # limiting factor, especially if they are X-axis fractional ticks like "/\"
        return max(min_printed_step, bin_width * (2 + tick_space * 2))
    return bin_width * (2 + tick_space)


def gen_position_subsets(positions: tuple, tick_step: Decimal) -> list[Sequence[Decimal]]:
    """Generate candidate label position subsets based on tick step digit.

    For tick steps starting with 1 or 2: generates every-5th subsets (5 variants).
    For tick steps starting with 5: generates every-2nd subsets (2 variants).
    """
    step_digit = tick_step.as_tuple().digits[0]  # leading digit of tick step: 1, 2, or 5
    # we want to pick different position subsets depending on whether we're advancing by
    # 1eX, 2eX, or 5eX:
    position_subsets = []
    if step_digit in (1, 2):
        # print on every fifth one, starting at 0..4
        position_subsets += list(util.sanitize_decimals(positions[start::5]) for start in range(5))
    elif step_digit == 5:
        # print on every second one, starting at 0 or 1
        position_subsets += list(util.sanitize_decimals(positions[start::2]) for start in range(2))
    return position_subsets


def label_ends_only(positions, tick_step, bin_width, accomodate_values, fmt):
    """See if printing just the labels for the first and last ticks will fit"""

    if not accomodate_values:
        # For Y axis / we don't care about printed widths
        return positions_to_labels((positions[0], positions[-1]), positions, fmt)

    end_positions = (positions[0], positions[-1])
    ends_printed = tuple(positions_to_labels(end_positions, [], fmt).values())

    half_len_first = len(ends_printed[0]) // 2
    half_len_last = (len(ends_printed[1]) + 1) // 2
    space_available = math.floor(tick_step / bin_width)

    if half_len_first + half_len_last <= space_available:
        # We can fit values on the first and last ticks
        return positions_to_labels(end_positions, positions, fmt)

    # Not enough space to print two values, so just print the first
    return positions_to_labels(end_positions[:1], positions, fmt)


def find_fitting_subset(position_subsets, ticks_per_bin, accomodate_values, fmt):
    """Find roundest label subset that fits within space constraints"""
    for position_subset in util.roundness_ordered(position_subsets):
        if not accomodate_values:  # it doesn't matter what the printed widths are, it will fit
            return position_subset
        # We're printing at most one value for every 2 ticks, so just make sure
        # that the printed values will not run over the adjacent ticks' area
        # Given the initial min_step logic, this will likely always be true
        printed_widths = (
            len(label) for label in positions_to_labels(position_subset, [], fmt).values()
        )
        allowed_width = ticks_per_bin * 2 - 2
        if max(printed_widths) <= allowed_width:
            return position_subset
    return tuple()


def gen_full_labels(value_range: ValueRange, num_bins, accomodate_values, tick_space, fmt):
    """Generate positions for labels (plain ticks & ticks with value)"""
    bin_width = (value_range.max - value_range.min) / num_bins

    if bin_width <= 0:
        # we don't have a sensible range for the axis values, so just have empty ticks
        return {}

    min_step = calc_min_step(value_range, bin_width, accomodate_values, tick_space, fmt)
    cur_tick_step = pick_step_size(min_step)

    while True:
        positions = tuple(gen_tick_values(value_range, cur_tick_step))

        if len(positions) == 0:
            # No suitable ticks/labels.
            if accomodate_values:
                # Printed value labels won't fit, try without them
                return gen_full_labels(value_range, num_bins, False, tick_space, "")
            # Nothing fits
            return {}
        if len(positions) == 1:
            return positions_to_labels(positions, [], fmt)

        position_subsets = gen_position_subsets(positions, cur_tick_step)

        # Check to see if all generated label subsets only have a single entry
        if max(len(subset) for subset in position_subsets) == 1:
            # Try to just label the ends:
            return label_ends_only(positions, cur_tick_step, bin_width, accomodate_values, fmt)

        best_subset = find_fitting_subset(
            position_subsets, cur_tick_step / bin_width, accomodate_values, fmt
        )

        if best_subset:
            return positions_to_labels(best_subset, positions, fmt)

        cur_tick_step = pick_step_size(float(cur_tick_step) * 1.01)


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
    if values_are_edges or num_bins == 1:
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
    labels: Optional[dict[FloatLike, str]] = (
        None  # map axis value to label (plus tick) at that value
    )
    label_fmt: str = "{}"  # format for generated labels
    border_line: bool = False  # embed ticks in a horizontal X-axis or vertical Y-axis line
    values_are_edges: bool = False  # N+1 values, indicating boundaries between pixels, not centers
    fractional_tick_pos: bool = False  # Use "▔", "▁", or "╱╲" for non-centered ticks

    def __init__(
        self,
        value_range: ValueRange | tuple[FloatLike, FloatLike],
        labels: Optional[dict[FloatLike, str]] = None,
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
            labels = gen_full_labels(
                self.value_range,
                num_rows,
                False,
                0,
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

                offset_frac = (float(label_values[0]) - float(row_min)) / float(row_max - row_min)
                # Try to avoid our cutoffs being exactly where roundoff errors can pop up and
                # cause inconsistent behavior. So 0.249 rather than 0.25, 0.751 rather than 0.75:
                if offset_frac < 0.249 and self.fractional_tick_pos:
                    tick_char = "▔"
                elif offset_frac > 0.751 and self.fractional_tick_pos:
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
            tick_space = 1 if self.fractional_tick_pos else 0
            labels = gen_full_labels(self.value_range, num_cols, True, tick_space, self.label_fmt)
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
                if self.fractional_tick_pos:
                    offset_frac = (label_values[0] - col_min) / (col_max - col_min)
                else:
                    offset_frac = 0.5  # not doing fractional tick positioning == center the tick

                add_x_tick(tick_line, col_idx + offset_frac, left_margin, num_cols)
                add_x_label(
                    label_line, labels[label_values[0]], col_idx + left_margin + offset_frac
                )

                label_values = label_values[1:]  # pop that first label since we added it

        return "".join(tick_line), "".join(label_line)
