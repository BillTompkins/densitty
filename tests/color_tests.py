import pytest
import sys

from densitty import ansi, ascii_art, plot, truecolor
import golden

ramp_data = [[x * 0.1 - 1 for x in range(110)], [10 - x * 0.1 for x in range(110)]]
color_maps = [
    "truecolor.GRAYSCALE",
    "truecolor.GRAYSCALE_LINEAR",
    "ansi.GRAYSCALE",
    "truecolor.BLUE_RED",
    "ansi.BLUE_RED",
    "truecolor.RAINBOW",
    "ansi.RAINBOW",
    "ansi.RAINBOW_16",
    "truecolor.FADE_IN",
    "ansi.FADE_IN",
    "truecolor.HOT",
    "ansi.HOT",
    "truecolor.COOL",
    "ansi.COOL",
]


@pytest.mark.parametrize("map_name", color_maps)
def test_colors(map_name, display=False):
    colormap = eval(map_name)
    p = plot.Plot(ramp_data[0:1], color_map=colormap, render_halfheight=False)
    golden.check(p.as_strings(), map_name)


@pytest.mark.parametrize("map_name", color_maps)
def test_halfheight_colors(map_name, display=False):
    colormap = eval(map_name)
    p = plot.Plot(ramp_data[0:1], color_map=colormap)
    golden.check(p.as_strings(), map_name + "_halfheight")


def display_colormap(colormap):
    color_mapping = eval(colormap)
    p = plot.Plot(ramp_data[0:1], color_map=color_mapping, render_halfheight=False)
    print(colormap)
    p.show()


def test_ascii(display=False):
    p = plot.Plot(
        ramp_data,
        min_data=0,
        max_data=10,
        color_map=ascii_art.EXTENDED,
    )
    name = "ascii-map"
    if display:
        print(name)
        p.show()
    else:
        golden.check(p.as_strings(), name)


def test_halfheight(display=False):
    name = f"halfheight"
    p = plot.Plot(
        ramp_data,
        min_data=0,
        max_data=10,
        color_map=truecolor.BLUE_RED,
    )
    if display:
        print(name)
        p.show()
    else:
        golden.check(p.as_strings(), name)


def test_halfheight_single_row(display=False):
    p = plot.Plot(
        ramp_data[0:1],
        min_data=0,
        max_data=10,
        color_map=truecolor.BLUE_RED,
    )
    name = "halfheight_single_row"
    if display:
        print(name)
        p.show()
    else:
        golden.check(p.as_strings(), name)


def test_auto_color_limits(display=False):
    p = plot.Plot(
        ramp_data[0:1],
        color_map=truecolor.BLUE_RED,
    )
    name = "auto_color_limits"
    if display:
        print(name)
        p.show()
    else:
        golden.check(p.as_strings(), name)


def test_auto_color_allzero(display=False):
    zero_data = [[0 for x in range(110)]]
    p = plot.Plot(
        zero_data,
        color_map=truecolor.BLUE_RED,
    )
    name = "auto_allzero"
    if display:
        print(name)
        p.show()
    else:
        golden.check(p.as_strings(), name)


if __name__ == "__main__":
    if "--oda" in sys.argv:
        truecolor.use_oda_colorcodes = True

    for cm in color_maps:
        display_colormap(cm)
    test_ascii(True)
    test_halfheight(True)
    test_halfheight_single_row(True)
    test_auto_color_limits(True)
    test_auto_color_allzero(True)
