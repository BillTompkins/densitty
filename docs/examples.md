Given a list of points:

```python
import random
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]
```
####  Generate a 2-D Histogram with 40x40 bins & axes using helper function, default colors, etc.
```python
# Use the 'histplot2d' helper function in 'detect.py' to pick color map based on terminal
# capabilities, bin the points into 40 bins in both X and Y, and make a plot with axes:
from densitty.detect import histplot2d

histplot2d(points, 40).show()
```
![Plot Output](./examples/example_1_histplot2d_basic.py.png)

####  Generate a 2-D Histogram by explicit binning & plot creation
```python
from densitty.binning import bin_with_size
from densitty.plot import Plot

# Bin the data into fixed-width 1x1 bins
binned, _, _= bin_with_size(points, 1)
# Plot the resulting histogram
Plot(binned).show()
```
![Plot Output](./examples/example_2_fixed_width_bins.py.png)

####  Add the axes:
```python
# bin in 1x1 bins, keeping the axis outputs
binned, x_axis, y_axis = bin_with_size(points, 1)

# include the axes with the plot:
p = Plot(binned, x_axis=x_axis, y_axis=y_axis)
p.show()
```
![Plot Output](./examples/example_3_add_axes.py.png)

####  Explicit binning boundaries, scaled output with specific colormap
```python
# Use explicit binning boundaries of -10..10
# scale up the output to 60x60, and use a blue-red 24b colormap
from densitty import truecolor

binned, x_axis, y_axis = bin_with_size(points, 1, ranges=((-10,10), (-10,10)))
p = Plot(binned, color_map=truecolor.BLUE_RED, x_axis=x_axis, y_axis=y_axis)
p.upscale((60,60)).show()
```
![Plot Output](./examples/example_4_do_scaling.py.png)

####  Bin with a finer bin size, use terminal-capability detection to pick a colormap, add border lines to axes:
```python
# Use finer bin size, add border lines to axes
# and use detect.plot, so terminal-capability detection is used to pick a color map
from densitty.detect import plot

binned, x_axis, y_axis = bin_with_size(points, (.25, .25), ranges=((-10,10), (-10,10)), border_line=True)
plot(binned, x_axis=x_axis, y_axis=y_axis).show()
```
![Plot Output](./examples/example_5_use_detect.py.png)

####  A PAM-4 Eye Diagram
```python
from densitty.detect import plot
from densitty.axis import Axis
# For e.g. PAM-4 Ethernet voltage vs fractional-UI data
# Given eye data in a list-of-lists-of-floats "array" named eye_data
# construct axes given the min/max of the bins along X and Y axes
# and plot
x_axis = Axis((-1, 1), border_line=True)
y_axis = Axis((-300, 300), border_line=True)
eye_plot = plot(eye_data, x_axis=x_axis, y_axis=y_axis)
eye_plot.show()
```
![Plot Output](./examples/example_6_eye_diagram.py.png)

