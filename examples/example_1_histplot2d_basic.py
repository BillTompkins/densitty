import random
random.seed(1)  # so that the data is consistent between runs

# START printed output
# Generate random data for plots:
import random
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# Use the helper function in 'detect.py' to pick color map based on terminal capabilities, bin the
# points into 40x40 bins, and make a plot with axes:
from densitty.detect import histplot2d

histplot2d(points, 40).show()
