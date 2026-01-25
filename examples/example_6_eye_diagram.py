# A PAM-4 Eye Diagram

from eye_plot import eye

eye_data = eye(96, 96, signal_levels=(-0.75, -0.25, 0.25, 0.75))
# START printed output
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
