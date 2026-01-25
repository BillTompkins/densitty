# Explicit binning boundaries, scaled output with specific colormap
import random

from densitty.binning import bin_with_size
from densitty.plot import Plot

random.seed(1)
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]
binned, x_axis, y_axis = bin_with_size(points, 1)

# START printed output
# Use explicit binning boundaries of -10..10
# scale up the output to 60x60, and use a blue-red 24b colormap
from densitty import truecolor

binned, x_axis, y_axis = bin_with_size(points, 1, ranges=((-10,10), (-10,10)))
p = Plot(binned, color_map=truecolor.BLUE_RED, x_axis=x_axis, y_axis=y_axis)
p.upscale((60,60)).show()
