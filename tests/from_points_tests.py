"""Tests for Plot.from_points() convenience method."""

import numpy as np
import pytest

from densitty import ansi, axis, plot, truecolor
from densitty.util import ValueRange
import golden


@pytest.fixture
def simple_points():
    """Generate simple uniformly distributed points."""
    points = []
    for x in np.arange(0.0, 1.0, 0.1):
        for y in np.arange(0.0, 1.0, 0.1):
            points.append((x, y))
    return points


@pytest.fixture
def diagonal_points():
    """Generate points along a diagonal line."""
    return [(x, x) for x in np.arange(0.0, 1.0, 0.01)]


@pytest.fixture
def random_points():
    """Generate random points with a fixed seed."""
    rng = np.random.default_rng(42)
    return [(x, y) for x, y in rng.random((200, 2))]


def test_from_points_default(simple_points):
    """Test from_points with default parameters."""
    p = plot.Plot.from_points(simple_points)
    assert p.data is not None
    assert len(p.data) > 0
    assert len(p.data[0]) > 0
    assert p.x_axis is not None
    assert p.y_axis is not None
    golden.check(p.as_strings())


def test_from_points_custom_bins(simple_points):
    """Test from_points with custom number of bins."""
    p = plot.Plot.from_points(simple_points, num_bins=(20, 10), auto_adjust_bins=False)
    assert len(p.data) == 10
    assert len(p.data[0]) == 20
    golden.check(p.as_strings())


def test_from_points_bin_sizes(diagonal_points):
    """Test from_points with explicit bin sizes."""
    p = plot.Plot.from_points(diagonal_points, bin_sizes=(0.1, 0.1))
    assert p.data is not None
    golden.check(p.as_strings())


def test_from_points_with_ranges(simple_points):
    """Test from_points with explicit ranges."""
    x_range = ValueRange(0, 1)
    y_range = ValueRange(0, 1)
    p = plot.Plot.from_points(
        simple_points,
        num_bins=(15, 15),
        ranges=(x_range, y_range),
        auto_adjust_bins=False,
    )
    assert len(p.data) == 15
    assert len(p.data[0]) == 15
    golden.check(p.as_strings())


def test_from_points_no_axes(simple_points):
    """Test from_points without automatic axis creation."""
    p = plot.Plot.from_points(simple_points, num_bins=(10, 10), create_axes=False)
    assert p.x_axis is None
    assert p.y_axis is None
    golden.check(p.as_strings())


def test_from_points_custom_colormap(random_points):
    """Test from_points with custom color map."""
    p = plot.Plot.from_points(
        random_points,
        num_bins=(30, 20),
        color_map=truecolor.FADE_IN,
    )
    assert p.color_map == truecolor.FADE_IN
    golden.check(p.as_strings())


def test_from_points_no_auto_adjust(simple_points):
    """Test from_points without auto-adjusting bins."""
    p = plot.Plot.from_points(
        simple_points,
        num_bins=(10, 10),
        auto_adjust_bins=False,
    )
    golden.check(p.as_strings())


def test_from_points_with_custom_axes(simple_points):
    """Test from_points with custom axis objects."""
    x_ax = axis.Axis((0, 1), border_line=True, values_are_edges=True)
    y_ax = axis.Axis((0, 1), border_line=True, values_are_edges=True)
    p = plot.Plot.from_points(
        simple_points,
        num_bins=(12, 12),
        x_axis=x_ax,
        y_axis=y_ax,
    )
    assert p.x_axis.border_line is True
    assert p.y_axis.border_line is True
    golden.check(p.as_strings())


def test_from_points_with_min_max_data(random_points):
    """Test from_points with min/max data values for normalization."""
    p = plot.Plot.from_points(
        random_points,
        num_bins=(25, 25),
        min_data=0,
        max_data=100,
    )
    assert p.min_data == 0
    assert p.max_data == 100
    golden.check(p.as_strings())


def test_from_points_flip_y_false(simple_points):
    """Test from_points with flip_y disabled."""
    p = plot.Plot.from_points(
        simple_points,
        num_bins=(10, 10),
        flip_y=False,
    )
    assert p.flip_y is False
    golden.check(p.as_strings())


def test_from_points_empty_data():
    """Test from_points with empty point list."""
    p = plot.Plot.from_points([], num_bins=(10, 10))
    # Should still create a plot, even if all bins are zero
    assert p.data is not None
    golden.check(p.as_strings())


def test_from_points_single_point():
    """Test from_points with a single point."""
    p = plot.Plot.from_points([(0.5, 0.5)], num_bins=(5, 5))
    assert p.data is not None
    golden.check(p.as_strings())


def test_from_points_mutually_exclusive_bins():
    """Test that specifying both num_bins and bin_sizes raises an error."""
    with pytest.raises(ValueError, match="Cannot specify both num_bins and bin_sizes"):
        plot.Plot.from_points(
            [(0.5, 0.5)],
            num_bins=(10, 10),
            bin_sizes=(0.1, 0.1),
        )


def test_from_points_upscale(random_points):
    """Test that from_points works with upscale method."""
    p = plot.Plot.from_points(random_points, num_bins=(20, 15))
    p_upscaled = p.upscale(max_size=(60, 30), keep_aspect_ratio=True)
    golden.check(p_upscaled.as_strings())


if __name__ == "__main__":
    # Visual tests for manual verification
    import random

    random.seed(42)
    points = [(random.random(), random.random()) for _ in range(500)]

    print("Default parameters:")
    plot.Plot.from_points(points).show()
    print("\n" + "=" * 80 + "\n")

    print("Custom bins (40x20):")
    plot.Plot.from_points(points, num_bins=(40, 20)).show()
    print("\n" + "=" * 80 + "\n")

    print("With bin sizes (0.05, 0.05):")
    plot.Plot.from_points(points, bin_sizes=(0.05, 0.05)).show()
    print("\n" + "=" * 80 + "\n")

    print("With colored output:")
    plot.Plot.from_points(points, num_bins=(50, 25), color_map=truecolor.HOT).show()
    print("\n" + "=" * 80 + "\n")

    print("Diagonal line pattern:")
    diag_points = [(x, x) for x in np.arange(0.0, 1.0, 0.01)]
    plot.Plot.from_points(diag_points, num_bins=(30, 30)).show()
