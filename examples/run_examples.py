separator = "\n\n" + "=" * 80

gendata = """
# Generate Data
import random

points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]
"""

print(gendata)
exec(gendata)

basic = """
# Bin the data and plot as 2-D histogram

from densitty.binning import bin_data
from densitty.plot import Plot

binned, x_axis, y_axis = bin_data(points, (1,1))
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
# Use explicit bin boundaries, and scale up the output
binned, x_axis, y_axis = bin_data(points, (1,1), ranges=((-10,10), (-10,10)))
p = Plot(binned, x_axis=x_axis, y_axis=y_axis)
p.upscale((60,60)).show()
"""
print(separator)
print(add_scaling)
exec(add_scaling)

use_detect = """
# Use finer bin size, add border lines to axes
# and use detect.plot, so terminal-capability detection is used to pick a color map
from densitty.detect import plot

binned, x_axis, y_axis = bin_data(points, (.25, .25), ranges=((-10,10), (-10,10)), border_line=True)
plot(binned, x_axis=x_axis, y_axis=y_axis).show()
"""
print(separator)
print(use_detect)
exec(use_detect)
