import copy
from decimal import Decimal
import os
import pytest


from densitty import ansi, ascii_art, axis, detect, lineart, plot, truecolor
import gen_norm_data
import golden

mock_terminal_size = os.terminal_size((100, 48))


def mock_get_terminal_size():
    return mock_terminal_size


def histlike():
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)

    y_axis = axis.Axis((Decimal(-1), Decimal(1)), border_line=False, values_are_edges=True)
    x_axis = axis.Axis((-1, 1), border_line=False, values_are_edges=True)

    # x_axis.fractional_tick_pos = True
    # y_axis.fractional_tick_pos = True

    my_plot = plot.Plot(
        data=data,
        color_map=truecolor.FADE_IN,
        # font_mapping = plot.overstrike_font,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    return my_plot


def bordered():
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)

    y_axis = axis.Axis(
        (Decimal(-1), Decimal(1)),
        border_line=True,
        values_are_edges=False,
        fractional_tick_pos=False,
    )
    x_axis = axis.Axis(
        (-1, 1),
        border_line=True,
        values_are_edges=False,
        fractional_tick_pos=False,
    )

    # x_axis.fractional_tick_pos = True
    # y_axis.fractional_tick_pos = True

    my_plot = plot.Plot(
        data=data,
        color_map=truecolor.FADE_IN,
        # font_mapping = plot.overstrike_font,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    return my_plot


@pytest.fixture
def simple_hist():
    return histlike()


@pytest.fixture
def border_nonhist():
    return bordered()


def test_simple_hist_toscreen(simple_hist, monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)

    upscaled = copy.deepcopy(simple_hist).upscale()
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_border_nonhist_toscreen(border_nonhist, monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)
    upscaled = copy.deepcopy(border_nonhist).upscale()
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_keepaspect(border_nonhist):
    upscaled = copy.deepcopy(border_nonhist).upscale(max_size=(150, 50), keep_aspect_ratio=True)
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_fitscreen(border_nonhist, monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)
    upscaled = copy.deepcopy(border_nonhist).upscale(max_expansion=(None, None))
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_fitscreen_noaxes(border_nonhist, monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)
    plt = copy.deepcopy(border_nonhist)
    plt.x_axis = None
    plt.y_axis = None
    upscaled = plt.upscale(max_expansion=(None, None))
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_reservemargin(border_nonhist, monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)
    upscaled = copy.deepcopy(border_nonhist).upscale(
        max_size=(-30, -30), max_expansion=(None, None)
    )
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_set_default_size(border_nonhist):
    plot.default_terminal_size = os.terminal_size((100, 100))
    upscaled = copy.deepcopy(border_nonhist).upscale(
        max_size=(-30, -30), max_expansion=(None, None)
    )
    upscaled.show()
    golden.check(upscaled.as_strings())


# The same things, but outputting to screen for visual check:
if __name__ == "__main__":
    histlike().upscale().show()
    bordered().upscale().show()
    bordered().upscale(max_size=(150, 50), keep_aspect_ratio=True).show()
    bordered().upscale(max_expansion=(None, None)).show()
    bordered().upscale(max_size=(-30, -30), max_expansion=(None, None)).show()
