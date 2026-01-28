# Generate a 2-D Histogram with 30x20 bins

import random
random.seed(1)  # so that the data is consistent between runs
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
# Use the 'histplot2d' helper function in 'detect.py' to pick color map based on terminal
# capabilities, bin the points into 30 X, 20 Y bins, 4 'pixels' per bin in X and Y

from densitty.detect import histplot2d

histplot2d(points[:200], (30,20), scale=4, colorscale=True).show()
