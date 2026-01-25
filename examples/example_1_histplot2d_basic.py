# Generate a 2-D Histogram with 40x40 bins & axes using helper function, default colors, etc.

import random
random.seed(1)  # so that the data is consistent between runs
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
# Use the 'histplot2d' helper function in 'detect.py' to pick color map based on terminal
# capabilities, bin the points into 40 bins in both X and Y, and make a plot with axes:
from densitty.detect import histplot2d

histplot2d(points, 40).show()
