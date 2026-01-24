# Bin the data into fixed-width bins and plot as 2-D histogram
import random
random.seed(1)
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]

# START printed output
from densitty.binning import bin_with_size
from densitty.plot import Plot

binned, x_axis, y_axis = bin_with_size(points, 1)
Plot(binned).show()
