from decimal import Decimal
import numpy as np


from densitty import ansi, ascii_art, axis, lineart, plot, truecolor
from densitty.util import ValueRange
import gen_norm_data

np.random.seed(0)
x = np.random.normal(0, 1.1, 5000)
y = np.random.normal(0, 1, 5000)

# Create 2D histogram
bins_x, bins_y = 20, 10
hist, x_edges, y_edges = np.histogram2d(x, y, bins=[bins_x, bins_y])

y_axis = axis.Axis(ValueRange(y_edges[0], y_edges[-1]), border_line=True, values_are_edges=True)
x_axis = axis.Axis(ValueRange(x_edges[0], x_edges[-1]), border_line=True, values_are_edges=True)

my_plot = plot.Plot(
    data=hist.tolist(),  # tolist() makes pypy happy, but isn't otherwise needed. TODO: use property vs type?
    color_map=truecolor.FADE_IN,
    y_axis=y_axis,
    x_axis=x_axis,
)
my_plot.upscale(max_size=(100, 48)).show()

x_axis.labels = {x_edges[0]: "first", x_edges[-1]: "last"}
my_plot.show()

x_axis.labels = None
my_plot.y_axis = None
my_plot.show()
