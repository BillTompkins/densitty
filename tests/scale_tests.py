import copy
from decimal import Decimal
import os
import pytest


from densitty import ansi, ascii_art, Axis, colorbar, detect, lineart, Plot, plotting, truecolor
import gen_norm_data
import golden


def histlike():
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)

    y_axis = Axis((Decimal(-1), Decimal(1)), border_line=False, values_are_edges=True)
    x_axis = Axis((-1, 1), border_line=False, values_are_edges=True)

    # x_axis.fractional_tick_pos = True
    # y_axis.fractional_tick_pos = True

    my_plot = Plot(
        data=data,
        color_map=truecolor.FADE_IN,
        # font_mapping = plotting.overstrike_font,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    return my_plot


def bordered():
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)

    y_axis = Axis(
        (Decimal(-1), Decimal(1)),
        border_line=True,
        values_are_edges=False,
        fractional_tick_pos=False,
    )
    x_axis = Axis(
        (-1, 1),
        border_line=True,
        values_are_edges=False,
        fractional_tick_pos=False,
    )

    # x_axis.fractional_tick_pos = True
    # y_axis.fractional_tick_pos = True

    my_plot = Plot(
        data=data,
        color_map=truecolor.FADE_IN,
        # font_mapping = plotting.overstrike_font,
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


def test_simple_hist_toscreen(simple_hist, set_screensize):
    upscaled = copy.deepcopy(simple_hist).upscale()
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_border_nonhist_toscreen(border_nonhist, set_screensize):
    upscaled = copy.deepcopy(border_nonhist).upscale()
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_keepaspect(border_nonhist):
    upscaled = copy.deepcopy(border_nonhist).upscale(max_size=(150, 50), keep_aspect_ratio=True)
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_fitscreen(border_nonhist, set_screensize):
    upscaled = copy.deepcopy(border_nonhist).upscale(max_expansion=(None, None))
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_fitscreen_noaxes(border_nonhist, set_screensize):
    plt = copy.deepcopy(border_nonhist)
    plt.x_axis = None
    plt.y_axis = None
    upscaled = plt.upscale(max_expansion=(None, None), keep_aspect_ratio=False)
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_reservemargin(border_nonhist, set_screensize):
    upscaled = copy.deepcopy(border_nonhist).upscale(
        max_size=(-30, -30), max_expansion=(None, None), keep_aspect_ratio=False
    )
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_maxsize_set_default_size(border_nonhist):
    plotting.default_terminal_size = os.terminal_size((100, 100))
    upscaled = copy.deepcopy(border_nonhist).upscale(
        max_size=-30, max_expansion=None, keep_aspect_ratio=False
    )
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_left_margin_no_axis():
    """left_margin() returns 0 when there is no y_axis"""
    data = [[1, 2, 3], [4, 5, 6]]
    plt = Plot(data=data, color_map=ansi.GRAYSCALE)
    assert plt.left_margin() == 0


def test_left_margin_halfheight():
    """left_margin() with y_axis in halfheight color mode"""
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)
    y_axis = Axis((-1, 1), border_line=False, values_are_edges=True)
    plt = Plot(data=data, color_map=truecolor.FADE_IN, y_axis=y_axis)
    assert plt.is_halfheight()
    margin = plt.left_margin()
    assert margin > 0
    golden.check(margin)


def test_left_margin_non_halfheight():
    """left_margin() with y_axis in non-halfheight (ASCII) mode"""
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)
    y_axis = Axis((-1, 1), border_line=False, values_are_edges=True)
    plt = Plot(data=data, color_map=ascii_art.DEFAULT, y_axis=y_axis)
    assert not plt.is_halfheight()
    margin = plt.left_margin()
    assert margin > 0
    golden.check(margin)


def test_left_margin_with_border():
    """left_margin() with bordered y_axis"""
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)
    y_axis = Axis((-1, 1), border_line=True, values_are_edges=True)
    plt = Plot(data=data, color_map=truecolor.FADE_IN, y_axis=y_axis)
    margin = plt.left_margin()
    assert margin > 0
    golden.check(margin)


def test_upscale_with_glued_on_plot(set_screensize):
    """upscale() also upscales a glued-on to_right Plot"""
    plt = bordered()
    colorbar.add_colorbar(plt)
    assert isinstance(plt.to_right, Plot)
    original_to_right_rows = len(plt.to_right.data)
    upscaled = plt.upscale()
    # The glued-on plot should have been upscaled in Y
    assert len(upscaled.to_right.data) > original_to_right_rows
    upscaled.show()
    golden.check(upscaled.as_strings())


def test_upscale_with_glued_on_plot_fixed_size(set_screensize):
    """upscale() with glued-on plot at a fixed max_size"""
    plt = histlike()
    colorbar.add_colorbar(plt)
    assert isinstance(plt.to_right, Plot)
    upscaled = plt.upscale(max_size=(100, 40), keep_aspect_ratio=True)
    upscaled.show()
    golden.check(upscaled.as_strings())


# The same things, but outputting to screen for visual check:
if __name__ == "__main__":
    histlike().upscale().show()
    bordered().upscale().show()
    bordered().upscale(max_size=(150, 50), keep_aspect_ratio=True).show()
    bordered().upscale(max_expansion=(None, None)).show()
    bordered().upscale(max_size=(-30, -30), max_expansion=(None, None)).show()
