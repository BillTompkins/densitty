# Generate a 2-D Histogram with fixed-size bins

import random
random.seed(1)  # so that the data is consistent between runs
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
from densitty import histplot2d

# Bin the points with an explicit bin size of 0.5
# rather than number or location. Since we don't provide a range for each axis, the
# range of data values is used
p = histplot2d(points, bin_size=0.5)
p.upscale().show()
