import pytest
from typing import Callable, NamedTuple

from densitty import ansi, axis, plotting, sixel, truecolor
import golden


def debug_output(s, end="\n"):
    print(repr(s))


def no_output(s, end="\n"):
    pass


@pytest.fixture()
def set_cell_height():
    sixel.Plot.set_cell_height(24)


class SixelPlotParams(NamedTuple):
    height: int
    x_border: bool
    y_border: bool
    colorscale: truecolor.Colormap_24b
    color_name: str
    datafunc: Callable[[int, int], float]
    data_name: str


testoptions = [
    SixelPlotParams(
        height=20,
        x_border=True,
        y_border=True,
        colorscale=truecolor.REV_RAINBOW,
        color_name="rev_rainbow",
        datafunc=lambda x, y: 0,
        data_name="allzero",
    ),
    SixelPlotParams(
        height=199,
        x_border=False,
        y_border=False,
        colorscale=truecolor.GRAYSCALE,
        color_name="gray",
        datafunc=lambda x, y: x + y,
        data_name="diagonal",
    ),
]


@pytest.mark.parametrize(
    "height, x_border, y_border, colorscale, color_name, datafunc, data_name", testoptions
)
def test_sixel_height(
    set_cell_height, height, x_border, y_border, colorscale, color_name, datafunc, data_name
):
    data = [[datafunc(x, y) for x in range(20)] for y in range(height)]
    y_axis = axis.Axis((-4, 0), border_line=x_border, values_are_edges=True)
    x_axis = axis.Axis((0, 4), border_line=y_border, values_are_edges=True)
    p = sixel.Plot(
        data,
        x_axis=x_axis,
        y_axis=y_axis,
        color_map=colorscale,
        fg_rgb=truecolor.WHITE,
        bg_rgb=truecolor.BLACK,
    )
    block, rows, cols = p.as_sixelblock()
    check = block.out(), rows, cols
    name = f"sixel-{height}-{x_border}-{y_border}-{color_name}-{data_name}"
    golden.check(check, name)


if __name__ == "__main__":
    cols, rows = 50, 25
    x_size, y_size = cols * sixel.Plot.get_cell_width(), rows * sixel.Plot.get_cell_height()

    data = [[(x + y) for x in range(x_size)] for y in range(y_size)]

    y_axis = axis.Axis((-4.1, -0.1), border_line=True, values_are_edges=True)
    x_axis = axis.Axis((0, 4), border_line=True, values_are_edges=True)
    p = sixel.Plot(
        data,
        x_axis=x_axis,
        y_axis=y_axis,
        color_map=truecolor.REV_RAINBOW,
        fg_rgb=truecolor.WHITE,
        bg_rgb=truecolor.BLACK,
    )

    p.show()
