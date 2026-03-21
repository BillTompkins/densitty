"""Sixel output support"""

import math
import os
from collections.abc import Callable, Sequence

from . import axis, detect, plotting, truecolor
from .util import batched


class SixelLine:
    """Accumulates sixel characters with run-length encoding compression."""

    MAX_RLE = 255

    def __init__(self):
        self._output = ""
        self.color: int | None = None
        self._pending_char: str | None = None
        self._pending_count: int = 0
        self.empty = True

    def _flush_pending(self):
        while self._pending_count > 0:
            n = min(self._pending_count, self.MAX_RLE)
            if n > 3:  # RLE only saves space if we have >3 in a row
                self._output += f"!{n}{self._pending_char}"
            else:
                self._output += self._pending_char * n
            self._pending_count -= n
        self._pending_char = None

    def add_char(self, ch, count=1):
        """Add a sixel character"""
        if ch == self._pending_char:
            self._pending_count += count
        else:
            self._flush_pending()
            self._pending_char = ch
            self._pending_count = count

    def set_color(self, color):
        """Set output color for subsequent sixels"""
        if self.color != color:
            self._flush_pending()
            self._output += f"#{color}"
            self.color = color

    def add_column(self, pixels: Sequence[bool]):
        """Add a sixel column from up to 6 pixel values (top to bottom)"""
        value = 0
        for i, bit in enumerate(pixels):
            if bit:
                value |= 1 << i
        ch = chr(63 + value)
        self.add_char(ch)
        if value != 0:
            self.empty = False

    def get(self) -> str:
        """Return the RLE-compressed sixel string, flushing any pending data."""
        self._flush_pending()
        return self._output


class MultiColorLine:
    """Up to six sixel-lines, to accomodate the required up-to-six simultaneous colors"""

    NUM_SIXEL_ROWS = 6  # there are six rows of pixels in a sixel
    NUM_LINES = 6  # up to 6 different lines of sixels, in order to specify per-pixel colors

    def __init__(self):
        self.width = 0
        self.lines = [SixelLine() for _ in range(self.NUM_LINES)]
        self.cur_line_with_color = {}  # map color index to the line that currently is that color

    def add(self, pixel_colors: Sequence[int]):
        """Adds up to six vertical pixels to the line"""

        # For each color in this six-pixel column, add it to an existing SixelLine if one already
        # has that color else change the color of an existing SixelLine.
        # Note:
        # This will preferentially keep the number of output lines low, which is maybe not optimal
        # if more lines are eventually required and a color is reused.
        for color in set(pixel_colors):
            # do we already have a line with this color?
            if color in self.cur_line_with_color:
                line = self.cur_line_with_color[color]
            else:
                # pick a line for this color
                for line in self.lines:
                    if line.color in pixel_colors:
                        # we need this line for another pixel color in this column
                        continue
                    if line.color is not None:
                        del self.cur_line_with_color[line.color]
                    line.set_color(color)
                    self.cur_line_with_color[color] = line
                    break
            line.add_column((c == color for c in pixel_colors))

        for line in self.lines:
            if line.color not in pixel_colors:
                line.add_column((False,) * self.NUM_SIXEL_ROWS)
        return self

    def out(self):
        """Returns sixel output for the multicolored lines"""
        output_lines = (line.get() for line in self.lines if not line.empty)
        return "$".join(output_lines)  # separate with "carriage return" symbol


def sixel_palette(colors: Sequence[truecolor.RGB]):
    """Sixel output to configure palette colors"""
    sixel_max_color = 100
    out = ""
    for idx, color in enumerate(colors):
        sixel_color = [round(sixel_max_color * component) for component in color]
        out += f"#{idx};2;{sixel_color[0]};{sixel_color[1]};{sixel_color[2]}"
    return out


class SixelBlock:
    """Collection of MultiColorLines, can add color data as a 2-D array of arrays"""

    def __init__(self, palette: Sequence[truecolor.RGB], data: Sequence[Sequence[int]] | None):
        self._palette = palette
        if data is not None:
            self._data = data
        else:
            self._data = []

    def add_below(self, new_lines: Sequence[Sequence[int]]):
        """Add the new_lines after the existing data lines"""
        self._data = tuple(self._data) + tuple(new_lines)
        return self

    def add_right(self, new_lines: Sequence[Sequence[int]]):
        """Add/Append the new_lines after each corresponding existing data line"""
        self._data = [tuple(left) + tuple(right) for left, right in zip(self._data, new_lines)]
        return self

    def add_left(self, new_lines: Sequence[Sequence[int]]):
        """Prepend the new_lines before each corresponding existing data line"""
        self._data = [tuple(left) + tuple(right) for left, right in zip(new_lines, self._data)]
        return self

    def out(self):
        """Produce the sixel output"""
        enter_sixel = "\033P0;1;0;q"  # Init sixel mode. p2=1 => don't overwrite background
        image_lines = []
        for six_rows in batched(self._data, 6):
            sixel_row = MultiColorLine()
            for column_data in zip(*six_rows):
                sixel_row.add(column_data)
            image_lines += [sixel_row.out()]
        image = "$-".join(image_lines)  # separate with "Carriage Return" + "Line Feed"

        exit_sixel = "\033\\"  # Exit sixel mode
        return enter_sixel + sixel_palette(self._palette) + image + exit_sixel


def axis_padding(width: int, height: int, x_border: bool, y_border: bool):
    """Return the 'corner' padding under the Y axis, to the left of the X axis"""
    blank_line = [[0] * (width + y_border)]
    if x_border and y_border:
        top = [[0] * width + [1]]
    elif x_border:
        top = blank_line
    else:
        top = []
    return top + blank_line * height


class Plot(plotting.Plot):
    """Plot with sixel output method"""

    # Height of text cell. If not set by user, we will try to detect it
    cell_height: int | None = None
    # Default calculator for text cell width based on the cell height: half, rounded down to even:
    cell_width: int | Callable = lambda cell_height: math.floor(cell_height / 4) * 2

    @classmethod
    def set_cell_height(cls, new_cell_height: int):
        """Set the height in pixels of a text character cell"""
        cls.cell_height = new_cell_height

    @classmethod
    def get_cell_height(cls):
        """Get the height in pixels of a text character cell"""
        if cls.cell_height is None:
            cls.cell_height = detect_sixel_size(overwrite_existing=False, right_side=True)
        return cls.cell_height

    @classmethod
    def set_cell_width(cls, new_cell_width: int | Callable[[int], int]):
        """Set the width in pixels of a text character cell.
        new_cell_width can be an integer value, or a function that returns the
        cell width given the cell height."""
        cls.cell_width = new_cell_width

    @classmethod
    def get_cell_width(cls):
        """Get the width in pixels of a text character cell"""
        if callable(cls.cell_width):
            return cls.cell_width(cls.get_cell_height())
        return cls.cell_width

    def __init__(self, *args, axis_fg=truecolor.WHITE, axis_bg=truecolor.BLACK, **kwargs):
        super().__init__(*args, **kwargs)
        self.axis_fg = axis_fg
        self.axis_bg = axis_bg
        self.add_colorbar = False

    def as_sixelblock(self):
        """Returns tuple of:
        - sixel output characters
        - expected # of text rows
        - expected # of text columns
        """
        height = len(self.data)
        width = len(self.data[0])

        rows = round(height / self.get_cell_height())
        cols = round(width / self.get_cell_width())

        axis_fg = self.axis_fg if self.axis_fg else truecolor.WHITE
        axis_bg = self.axis_bg if self.axis_bg else truecolor.BLACK

        sixel_block = SixelBlock(self.color_map.palette(axis_fg, axis_bg), self.data_paletteized())

        if self.y_axis:
            y_tick_width = self.get_cell_width() - (1 * self.y_axis.border_line)
            y_axis_border = self.y_axis.render_as_y_pixels(y_tick_width, rows, height)
            if self.flip_y:
                y_axis_border = reversed(y_axis_border)
            sixel_block.add_left(y_axis_border)

        if self.x_axis:
            x_tick_height = self.get_cell_height() // 2
            x_axis_border = self.x_axis.render_as_x_pixels(x_tick_height, cols, width)
            if self.y_axis:
                corner = axis_padding(
                    y_tick_width, x_tick_height, self.x_axis.border_line, self.y_axis.border_line
                )
                sixel_block.add_below(c + x for c, x in zip(corner, x_axis_border))
            else:
                sixel_block.add_below(x_axis_border)
        return sixel_block, rows, cols

    def show_colorbar(self, prefix=""):
        """Display a horizontal colorbar via sixels"""

        min_value, max_value = self.data_limits()

        colorbar_labels = {
            min_value: str(min_value),
            max_value: str(max_value),
        }
        colorbar_axis = axis.Axis(
            value_range=(min_value, max_value),
            labels=colorbar_labels,
            values_are_edges=False,
            border_line=False,
        )
        bar_width = len(self.data[0])
        bar_height = 10
        gradient_data = [[i / (bar_width - 1) for i in range(bar_width)]] * bar_height

        colorbar_plot = Plot(
            data=gradient_data,
            color_map=self.color_map,
            render_halfheight=False,
            font_mapping=self.font_mapping,
            x_axis=colorbar_axis,
            min_data=0,
            max_data=1,
            flip_y=False,
        )
        colorbar_plot.show(prefix=prefix)

    def show(self, prefix="", printer=print):
        sixel_block, rows, cols = self.as_sixelblock()

        if self.y_axis:
            # Print the text of the Y axis:
            #
            y_axis_text = self.y_axis.render_as_y(rows, pad_top=0, pad_bot=0, flip=self.flip_y)

            y_axis_labels = [
                prefix + y[:-1] for y in y_axis_text
            ]  # add prefix & strip trailing "-"
            printer("\n".join(y_axis_labels), end="")

            # cursor is now after the bottom Y axis text line. Move to after the top Y axis line:
            printer(f"\033[{len(y_axis_labels) - 1}A", end="")
            y_axis_margin = len(y_axis_text[0])
        else:
            print(prefix, end="")
            y_axis_margin = 0
        printer(sixel_block.out(), end="")

        if self.x_axis:
            _, x_axis_text_labels = self.x_axis.render_as_x(cols, y_axis_margin)
            printer(prefix + x_axis_text_labels)

        if self.add_colorbar:
            print("")
            bar_prefix = prefix + " " * y_axis_margin
            self.show_colorbar(prefix=bar_prefix)


def count_text_rows_for_sixels(sixel_lines: int, start_row: int):
    """How many text rows do we move down for N sixel lines of output?"""
    s = SixelBlock([truecolor.BLACK, truecolor.BLACK], [[1]] * sixel_lines)
    print(s.out(), end="")
    post_cursor_pos = detect.get_cursor_pos()
    num_text_lines = post_cursor_pos[1] - start_row
    return num_text_lines


def detect_sixel_size(overwrite_existing=False, right_side=True):
    """Determine pixels per character / Ratio of Sixel output to character output
    Parameters
    ----------
     overwrite_existing : bool
         Overwrite the existing screen contents (two characters)
         rather than scrolling the window by two lines.
     right_side : bool
         Overwrite characters in the next-to-last column, rather than the first.

     returns: number of vertical pixels per character
    """
    terminal_size = os.get_terminal_size()

    if not overwrite_existing:
        # Make space for the test output. We'll reset to _before_ that output afterwards
        print("\n")  # Move down two lines (and scroll terminal if we're at the bottom)

    pre_cursor_row = terminal_size.lines - 2
    if right_side:
        pre_cursor_col = terminal_size.columns - 1
    else:
        pre_cursor_col = 1

    step = 1
    for _ in range(10):
        step *= 2
        detect.set_cursor_pos(pre_cursor_col, pre_cursor_row)
        rows = count_text_rows_for_sixels(step, pre_cursor_row)
        if rows > 1:
            min_pos = step // 2
            step = step // 4
            break
    else:
        raise OSError("Unable to determine sixels/pixels per character")

    while step > 0:
        detect.set_cursor_pos(pre_cursor_col, pre_cursor_row)
        rows = count_text_rows_for_sixels(min_pos + step, pre_cursor_row)
        if rows == 1:
            min_pos += step
        step = step // 2

    detect.set_cursor_pos(pre_cursor_col, pre_cursor_row)
    print(" \033[D\033[B ", end="")  # erase the sixel output (space, left, down, space)
    if overwrite_existing:
        print("")
    else:
        detect.set_cursor_pos(1, pre_cursor_row)

    # "min_pos" now has the number of sixel rows that don't cause a "spill" into the next text row
    return min_pos


def plot(data, colors=detect.FADE_IN, colorscale=False, **plotargs):
    """Helper function used with detect.py functions to produce a Plot object"""
    if "axis_fg" not in plotargs:
        plotargs["axis_fg"] = truecolor.WHITE
    if "axis_bg" not in plotargs:
        plotargs["axis_bg"] = truecolor.BLACK
    colormap24b = colors[detect.ColorSupport.ANSI_24BIT]
    the_plot = Plot(data, color_map=colormap24b, **plotargs)

    if colorscale:
        the_plot.add_colorbar = True

    return the_plot
