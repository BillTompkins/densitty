"""In-terminal 2-D histogram/density/heatmap plotting"""

from .detect import densityplot2d, grid_heatmap, histplot2d, plot
from .detect import GRAYSCALE, FADE_IN, RAINBOW, REV_RAINBOW
from .axis import Axis
from .plotting import Plot
from .colorbar import make_colorbar
from .binning import histogram2d
from .smoothing import smooth2d
