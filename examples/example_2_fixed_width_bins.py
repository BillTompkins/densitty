# Generate a 2-D Histogram by explicit binning & plot creation

import random
random.seed(1)
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
from densitty.binning import bin_with_size
from densitty.plot import Plot

# Bin the data into fixed-width 1x1 bins
binned, _, _= bin_with_size(points, 1)
# Plot the resulting histogram
Plot(binned).show()
