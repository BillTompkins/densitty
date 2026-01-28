# Generate a Grid-style heatmap with user-specified labels

import random
random.seed(1)  # so that the data is consistent between runs
# START printed output
# random values for the heatmap, in 10x8 grid
values = [[random.triangular(-2, 10, 1) for _ in range(10)] for _ in range(8)]

from densitty import grid_heatmap, make_colorbar

plt = grid_heatmap(values,
                   x_labels=[f"s{i}" for i in range(1,11)],
                   y_labels=["Frogs", "Lizards", "Humans", "Antelope", "Bears", "Ants", "Penguins", "Sloths"],
                   )
plt.show()
# add a color scale based on the plot data, indented by the plot's left margin:
scale = make_colorbar(plt, label_fmt="{:0.2}")
scale.show(prefix=" " * plt.left_margin())
