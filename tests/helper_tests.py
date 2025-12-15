import os
import pytest
import random

from densitty import axis, binning, detect

import gen_norm_data
import golden


mock_terminal_size = os.terminal_size((100, 48))


def mock_get_terminal_size():
    return mock_terminal_size


@pytest.fixture()
def points():
    """Example data"""
    random.seed(1)
    return [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]


def test_histplot2d_1(points):
    """Simplest usage"""
    plt = detect.histplot2d(points)
    plt.show()
    golden.check(plt.as_strings())


def test_histplot2d_2(points):
    """40x40 bins, Tell it the data is ranging from -10..10"""
    plt = detect.histplot2d(points, 40, ((-10, 10), (-10, 10)))
    plt.show()
    golden.check(plt.as_strings())


def test_histplot2d_3(points, monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)
    plt = detect.histplot2d(points, scale=True)
    plt.show()
    golden.check(plt.as_strings())


def test_histplot2d_4(points, monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)
    plt = detect.histplot2d(points, scale=5)
    plt.show()
    golden.check(plt.as_strings())
