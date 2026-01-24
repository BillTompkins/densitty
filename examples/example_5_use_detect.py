import random

from densitty.binning import bin_with_size

random.seed(1)
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
# Use finer bin size, add border lines to axes
# and use detect.plot, so terminal-capability detection is used to pick a color map
from densitty.detect import plot

binned, x_axis, y_axis = bin_with_size(points, (.25, .25), ranges=((-10,10), (-10,10)), border_line=True)
plot(binned, x_axis=x_axis, y_axis=y_axis).show()
