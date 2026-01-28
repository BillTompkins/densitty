# Generate a 2-D Density plot sized to screen width, default colors & plot/axis options

import random
random.seed(1)  # so that the data is consistent between runs
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
# Use 'densityplot2d' to pick color map based on terminal capabilities, pick a smoothing
# kernel to use, and make a density plot of the first 200 points with the plot size
# determined by the terminal window's width:
from densitty import densityplot2d

densityplot2d(points[:200]).show()
