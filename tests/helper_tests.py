import os
import pytest
import random
from unittest import mock

from densitty import axis, binning, detect, smoothing

import gen_norm_data
import golden

mock_terminal_size = os.terminal_size((100, 48))


def mock_get_terminal_size():
    return mock_terminal_size


@pytest.fixture()
def force_truecolor(monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "3")


@pytest.fixture()
def set_screensize(monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)


@pytest.fixture()
def points():
    """Example data"""
    random.seed(1)
    return [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]


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
    bins = tuple(x * .25 for x in range(-40, 41))
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
