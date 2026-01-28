# Generate a 2-D Histogram with fixed-size bins

import random
random.seed(1)  # so that the data is consistent between runs
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
from densitty import bin_with_size, plot

# Bin the points with an explicit bin size of 0.5
# rather than number or location of bins as histplot2d takes
binned, x_axis, y_axis = bin_with_size(points, 0.5, border_line=True)

# Plot the resulting 2-D histogram,
p = plot(binned, colorscale=True, x_axis=x_axis, y_axis=y_axis).upscale()
p.show()
