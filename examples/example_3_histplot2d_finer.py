# Generate a 2-D Histogram of more points with 60x40 bins

import random
random.seed(1)  # so that the data is consistent between runs
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
# Bin all of the points with an explicit bin size (rather than number of bins), and plot the
# result as a 2-D histogram:
from densitty import histplot2d

histplot2d(points, (60,40), scale=2, colorscale=True).show()
