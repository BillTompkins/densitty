<h1 align="center">densitty</h1>
<h2 align="center"> Terminal-based 2-D Histogram, Density Plots, and Heatmaps</h2>

Generate 2-D histograms (density plots, heat maps, eye diagrams) similar to [matplotlib's hist2d](https://matplotlib.org/stable/gallery/statistics/hist.html "hist2d"), but with output in the terminal, and no external dependencies.

## Examples
Given a list of points:

```python
import random
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]
```

#### Generate a 2-D Histogram:
```python
from densitty.binning import bin_data
from densitty.plot import Plot

binned, x_range, y_range = bin_data(points, (1,1))
Plot(binned).show()
```
Looks like:

![Plot Output](./examples/hist2d-basic.png)

#### Add some axes:
```python
from densitty.axis import Axis

# The bins in a histogram are typically labeled on the edges, not the bin centers
x_axis = Axis(x_range, values_are_edges=True)
y_axis = Axis(y_range, values_are_edges=True)

p = Plot(binned, x_axis=x_axis, y_axis=y_axis)
p.show()
```
![Plot Output](./examples/hist2d-axes.png)

#### Specify explicit boundaries for the binning, and scale up the output
```python
binned, x_range, y_range = bin_data(points, (1,1), ranges=((-10,10), (-10,10)))
x_axis = Axis(x_range, values_are_edges=True)
y_axis = Axis(y_range, values_are_edges=True)
p = Plot(binned, x_axis=x_axis, y_axis=y_axis)
p.upscale((60,60)).show()
```
![Plot Output](./examples/hist2d-scaled.png)


#### Bin with a finer bin size, use terminal-capability detection to pick a colormap, add border lines to axes:
```python
from densitty.detect import plot

binned, x_range, y_range = bin_data(points, (.25, .25), ranges=((-10,10), (-10,10)))
plot(binned, x_axis=Axis(x_range, border_line=True), y_axis=Axis(y_range, border_line=True)).show()
```
![Plot Output](./examples/hist2d-finer-color-borderline.png)

TODO: Add description, comments on usage

TODO: Add API notes
