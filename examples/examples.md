Given a list of points:

```python
import random
points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]
```

#### Generate a 2-D Histogram with 40x40 bins & axes using helper function, default colors, etc.
```
from densitty.detect import histplot2d

histplot2d(points, 40).show()
```
![Plot Output](./hist2d-helper.png)

#### Generate a 2-D Histogram by explicit binning & plot creation:
```python
from densitty.binning import bin_data
from densitty.plot import Plot

# bin the points into 1x1-sized bins:
binned, _, _ = bin_with_size(points, 1)

# Create a plot with that data and display it:
Plot(binned).show()
```
Output:

![Plot Output](./hist2d-basic.png)

#### Add some axes:
```python

binned, x_axis, y_axis = bin_with_size(points, 1)

p = Plot(binned, x_axis=x_axis, y_axis=y_axis)
p.show()
```
![Plot Output](./hist2d-axes.png)

#### Specify explicit boundaries for the binning, scale up the output size to 60x60, and specify colormap:
```python
binned, x_axis, y_axis = bin_with_size(points, 1, ranges=((-10,10), (-10,10)))
p = Plot(binned, color_map=truecolor.BLUE_RED, x_axis=x_axis, y_axis=y_axis)
p.upscale((60,60)).show()
```
![Plot Output](./hist2d-scaled.png)


#### Bin with a finer bin size, use terminal-capability detection to pick a colormap, add border lines to axes:
```python
from densitty.detect import plot

binned, x_axis, y_axis = bin_with_size(points, (.25, .25), ranges=((-10,10), (-10,10)), border_line=True)
plot(binned, x_axis, y_axis).show()
```
![Plot Output](./hist2d-finer-color-borderline.png)

#### A PAM-4 Eye Diagram

```python
eye_data = eye(96, 96, signal_levels=(-0.75, -0.25, 0.25, 0.75))
x_axis = Axis((-1, 1), border_line=True)
y_axis = Axis((-300, 300), border_line=True)
eye_plot = plot(eye_data, x_axis=x_axis, y_axis=y_axis)
eye_plot.show()
```
![Plot Output](./eyeplot.png)
