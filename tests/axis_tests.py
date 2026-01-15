from decimal import Decimal
import itertools
import pytest
import sys

from densitty import ansi, ascii_art, axis, lineart, plot, truecolor
from densitty.util import make_value_range, ValueRange

import gen_norm_data
import golden


@pytest.fixture(autouse=True)
def data():
    """Example data"""
    return gen_norm_data.gen_norm(num_rows=50, num_cols=50, width=0.3, height=0.15, angle=0.5)


# Some different value ranges to exercise fractional tick options
ranges = (make_value_range((-1, x)) for x in [0, 0.1, 1, 1.5, 2, 10])


combinations = itertools.product(
    [False, True],  # render_halfheight
    ranges,
    [lineart.basic_font, lineart.extended_font, lineart.ascii_font],
    [False, True],  # x_axis.border_line
    [False, True],  # y_axis.border_line
    [False, True],  # y_axis.values_are_edges
    [False, True],  # x_axis.values_are_edges
)


def idfn(arg):
    if isinstance(arg, bool):
        return f"{arg}"
    if isinstance(arg, ValueRange):
        return f"({arg.min}-{arg.max})"
    return {"|": "ascii", "│": "basic", None: "ext"}[arg.get("╷", None)]


@pytest.mark.parametrize(
    "halfheight,axis_range,fontmap,x_border,y_border,x_edges,y_edges", combinations, ids=idfn
)
def test_axes(data, halfheight, axis_range, fontmap, x_border, y_border, x_edges, y_edges):
    """Combiniatorial check of axis options"""
    x_axis = axis.Axis(
        axis_range, border_line=x_border, values_are_edges=x_edges, fractional_tick_pos=True
    )
    y_axis = axis.Axis(
        axis_range, border_line=y_border, values_are_edges=y_edges, fractional_tick_pos=True
    )
    p = plot.Plot(
        data,
        color_map=ansi.GRAYSCALE,
        render_halfheight=halfheight,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    name = "test_axes-" + "-".join(
        str(x)
        for x in [
            halfheight,
            idfn(axis_range),
            idfn(fontmap),
            x_border,
            y_border,
            x_edges,
            y_edges,
        ]
    )
    print(name)
    p.show()
    golden.check(p.as_strings(), name)


ascii_combinations = itertools.product(
    [False, True],  # x_axis.border_line
    [False, True],  # y_axis.border_line
    [False, True],  # y_axis.values_are_edges
    [False, True],  # x_axis.values_are_edges
)


@pytest.mark.parametrize("x_border,y_border,x_edges,y_edges", ascii_combinations)
def test_axes_ascii(data, x_border, y_border, x_edges, y_edges):  # , request):
    """Combiniatorial check of axis options"""
    x_axis = axis.Axis(ValueRange(-1, 1), border_line=x_border, values_are_edges=x_edges)
    y_axis = axis.Axis(
        ValueRange(Decimal(-1), Decimal(1)), border_line=y_border, values_are_edges=y_edges
    )
    p = plot.Plot(
        data,
        color_map=ascii_art.EXTENDED,
        render_halfheight=False,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    name = "test_axes_ascii-" + "-".join(str(x) for x in [x_border, y_border, x_edges, y_edges])
    print(name)
    p.show()
    golden.check(p.as_strings(), name)


def test_axes_small():
    minidata = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    x_axis = axis.Axis((-1, 1), border_line=True)
    y_axis = axis.Axis((-1, 1), border_line=True)
    p = plot.Plot(
        minidata,
        color_map=ansi.GRAYSCALE,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    print("test_axes_small")
    p.show()
    golden.check(p.as_strings())


def test_axes_labelsgiven(data):
    x_axis = axis.Axis((-1, 1), labels={-1: "AAA", 1: "BBB"}, border_line=True)
    y_axis = axis.Axis((-1, 1), labels={-1: "foo", 1: "bar"}, border_line=True)
    p = plot.Plot(
        data,
        color_map=ansi.GRAYSCALE,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    print("test_axes_labelsgiven")
    p.show()
    golden.check(p.as_strings())


def test_axes_1():
    """Small plot with egregiously large values that won't fit"""
    dataset = gen_norm_data.gen_norm(num_rows=10, num_cols=10, width=0.3, height=0.15, angle=0.5)
    x_axis = axis.Axis((10000000000, 100000000000))
    y_axis = axis.Axis((0, 1))
    p = plot.Plot(
        dataset,
        color_map=ansi.GRAYSCALE,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    p.show()
    golden.check(p.as_strings())


def test_axes_2():
    """Very small plot"""
    """Small plot with large values that won't fit well"""
    dataset = gen_norm_data.gen_norm(num_rows=7, num_cols=7, width=0.3, height=0.15, angle=0.5)
    x_axis = axis.Axis((10, 1000))
    y_axis = axis.Axis((0, 1))
    p = plot.Plot(
        dataset,
        color_map=ansi.GRAYSCALE,
        y_axis=y_axis,
        x_axis=x_axis,
    )
    p.show()
    golden.check(p.as_strings())


def test_axes_3():
    """Try to excercise edge-case code path"""
    dataset = gen_norm_data.gen_norm(num_rows=11, num_cols=18, width=0.3, height=0.15, angle=0.5)
    x_axis = axis.Axis((0, 800))
    y_axis = axis.Axis((0, 1))
    p = plot.Plot(
        dataset,
        color_map=ansi.GRAYSCALE,
        y_axis=y_axis,
        x_axis=x_axis,
    )
    p.show()
    golden.check(p.as_strings())


def test_axes_single_pixel():
    """Single-pixel plot"""
    dataset = [[0]]
    x_axis = axis.Axis((-0.2, 1), fractional_tick_pos=True)
    y_axis = axis.Axis((0, 1))
    p = plot.Plot(
        dataset,
        color_map=ansi.GRAYSCALE,
        y_axis=y_axis,
        x_axis=x_axis,
    )
    p.show()
    golden.check(p.as_strings())


def test_axes_invalid_pick_step_size():
    """Test exception path"""
    with pytest.raises(ValueError):
        axis.pick_step_size(0)


def test_axes_invalid_1(data):
    """Test zero-length axis range"""
    x_axis = axis.Axis((0, 0))
    y_axis = axis.Axis((0, 0))
    p = plot.Plot(
        data,
        color_map=ansi.GRAYSCALE,
        y_axis=y_axis,
        x_axis=x_axis,
    )
    p.show()
    golden.check(p.as_strings())


if __name__ == "__main__":
    from rich import traceback

    test_axes_3()
    sys.exit()
    dataset = gen_norm_data.gen_norm(num_rows=50, num_cols=50, width=0.3, height=0.15, angle=0.5)
    for args in combinations:
        test_axes(dataset, *args)

    test_axes_small()
    test_axes_labelsgiven(dataset)

    x_axis = axis.Axis((-10_000_000_000_000, 10_000_000_000_000))
    y_axis = axis.Axis((-1, 1))
    p = plot.Plot(
        dataset,
        color_map=ansi.GRAYSCALE,
        y_axis=y_axis,
        x_axis=x_axis,
        min_data=-0.2,
    )
    p.show()
    x_axis.label_fmt = "{:.2e}"
    p.show()
