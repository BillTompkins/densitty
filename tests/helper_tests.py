import pytest
from unittest import mock

from densitty import axis, binning, detect, smoothing

import gen_norm_data
import golden


def test_histplot2d_1(points, force_truecolor):
    """Simplest usage"""
    plt = detect.histplot2d(points)
    plt.show()
    golden.check(plt.as_strings())


def test_histplot2d_2(points, force_truecolor):
    """40x40 bins, Tell it the data is ranging from -10..10"""
    plt = detect.histplot2d(points, bins=40, ranges=((-10, 10), (-10, 10)))
    plt.show()
    golden.check(plt.as_strings())


def test_histplot2d_3(points, force_truecolor, set_screensize):
    plt = detect.histplot2d(points, scale=True)
    plt.show()
    golden.check(plt.as_strings())


def test_histplot2d_4(points, force_truecolor, set_screensize):
    plt = detect.histplot2d(points, scale=5)
    plt.show()
    golden.check(plt.as_strings())


def test_densityplot2d_1(points, force_truecolor, set_screensize):
    plt = detect.densityplot2d(points[:200])
    plt.show()
    golden.check(plt.as_strings())


def test_densityplot2d_2(points, force_truecolor, set_screensize):
    plt = detect.densityplot2d(points[:200], bins=40, ranges=((-10, 10), (-10, 10)))
    plt.show()
    golden.check(plt.as_strings())


def test_densityplot2d_3(points, force_truecolor, set_screensize):
    kernel = smoothing.gaussian_with_sigmas(1, 1)
    plt = detect.densityplot2d(points[:200], kernel=kernel, bins=40, ranges=((-10, 10), (-10, 10)))
    plt.show()
    golden.check(plt.as_strings())


def test_densityplot2d_4(points, force_truecolor, set_screensize):
    bins = tuple(x * 0.25 for x in range(-40, 41))
    plt = detect.densityplot2d(points[:200], bins=bins)
    plt.show()
    golden.check(plt.as_strings())


def test_detect_plot(force_truecolor):
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)
    y_axis = axis.Axis((-1, 1), border_line=True)
    x_axis = axis.Axis((-1, 1), border_line=True)
    plt = detect.plot(data, y_axis=y_axis, x_axis=x_axis)
    plt.show()
    golden.check(plt.as_strings())


def test_detect_plot_with_bar(force_truecolor):
    data = gen_norm_data.gen_norm(num_rows=20, num_cols=20, width=0.3, height=0.15, angle=0.5)
    y_axis = axis.Axis((-1, 1), border_line=True)
    x_axis = axis.Axis((-1, 1), border_line=True)
    plt = detect.plot(
        data, min_data=0.0, max_data=1.0, y_axis=y_axis, x_axis=x_axis, colorscale=True
    )
    plt.show()
    golden.check(plt.as_strings())


def test_grid_heatmap(force_truecolor, set_screensize):
    import random

    random.seed(1)
    values = [[random.triangular(-2, 10, 1) for _ in range(10)] for _ in range(8)]
    plt = detect.grid_heatmap(
        values,
        x_labels=[f"s{i}" for i in range(1, 11)],
        y_labels=["Frogs", "Lizards", "Humans", "Antelope", "Bears", "Ants", "Penguins", "Sloths"],
    )
    plt.show()
    golden.check(plt.as_strings())


def test_grid_heatmap_custom_cell_size(force_truecolor, set_screensize):
    data = [[1, 2, 3], [4, 5, 6]]
    plt = detect.grid_heatmap(
        data,
        x_labels=["A", "B", "C"],
        y_labels=["X", "Y"],
        max_cell_size=8,
    )
    plt.show()
    golden.check(plt.as_strings())


def test_grid_heatmap_mismatched_y_labels():
    data = [[1, 2], [3, 4]]
    with pytest.raises(ValueError, match="Y labels"):
        detect.grid_heatmap(data, x_labels=["A", "B"], y_labels=["X"])


def test_grid_heatmap_mismatched_x_labels():
    data = [[1, 2], [3, 4]]
    with pytest.raises(ValueError, match="X labels"):
        detect.grid_heatmap(data, x_labels=["A"], y_labels=["X", "Y"])
