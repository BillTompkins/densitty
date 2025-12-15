separator = "\n\n" + "=" * 80

gendata = """
# Generate Data
import random

points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]
"""

print(gendata)
exec(gendata)

use_detect = """
# Use the helper function in 'detect.py' to pick color map based on terminal capabilities, bin the
# points into 40x40 bins, and make a plot with axes:
from densitty.detect import histplot2d

histplot2d(points, 40).show()
"""
print(separator)
print(use_detect)
exec(use_detect)

basic = """
# Bin the data into fixed-width bins and plot as 2-D histogram

from densitty.binning import bin_with_size
from densitty.plot import Plot

binned, x_axis, y_axis = bin_with_size(points, 1)
Plot(binned).show()
"""
print(separator)
print(basic)
exec(basic)


add_axes = """
# Add axes
p = Plot(binned, x_axis=x_axis, y_axis=y_axis)
p.show()
"""
print(separator)
print(add_axes)
exec(add_axes)


add_scaling = """
# Use explicit bin boundaries, scale up the output, and use a blue-red colormap
from densitty import truecolor

binned, x_axis, y_axis = bin_with_size(points, 1, ranges=((-10,10), (-10,10)))
p = Plot(binned, color_map=truecolor.BLUE_RED, x_axis=x_axis, y_axis=y_axis)
p.upscale((60,60)).show()
"""
print(separator)
print(add_scaling)
exec(add_scaling)

use_detect = """
# Use finer bin size, add border lines to axes
# and use detect.plot, so terminal-capability detection is used to pick a color map
from densitty.detect import plot

binned, x_axis, y_axis = bin_with_size(points, (.25, .25), ranges=((-10,10), (-10,10)), border_line=True)
plot(binned, x_axis=x_axis, y_axis=y_axis).show()
"""
print(separator)
print(use_detect)
exec(use_detect)
