"""Tests for colorbar generation."""

import pytest

from densitty import ansi, colorbar, plot

import gen_norm_data
import golden


@pytest.fixture
def sample_data():
    """Example data for colorbar tests."""
    return gen_norm_data.gen_norm(num_rows=20, num_cols=40, width=0.3, height=0.15, angle=0.5)


def test_colorbar_basic(sample_data):
    """Test colorbar with typical plot."""
    source = plot.Plot(
        sample_data,
        color_map=ansi.RAINBOW,
        render_halfheight=True,
        min_data=-50,
        max_data=50,
    )
    cb = colorbar.colorbar(source)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_label_format(sample_data):
    """Test colorbar with custom label formatting."""
    source = plot.Plot(
        sample_data,
        color_map=ansi.GRAYSCALE,
        render_halfheight=True,
        min_data=0.0,
        max_data=1.0,
    )
    cb = colorbar.colorbar(source, label_fmt="{:.2f}")
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_narrow():
    """Test colorbar with narrow width."""
    narrow_data = [[i for i in range(10)] for _ in range(5)]
    source = plot.Plot(
        narrow_data,
        color_map=ansi.GRAYSCALE,
        render_halfheight=True,
        min_data=0,
        max_data=10,
    )
    cb = colorbar.colorbar(source)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_infer_limits():
    """Test colorbar when min_data/max_data not set on source plot."""
    data = [[0, 5, 10], [1, 6, 11], [2, 7, 12]]
    source = plot.Plot(
        data,
        color_map=ansi.GRAYSCALE,
        render_halfheight=True,
    )
    cb = colorbar.colorbar(source)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_vertical_basic(sample_data):
    """Test vertical colorbar."""
    source = plot.Plot(
        sample_data,
        color_map=ansi.FADE_IN,
        render_halfheight=True,
        min_data=0,
        max_data=100,
    )
    cb = colorbar.colorbar(source, vertical=True)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_vertical_label_format(sample_data):
    """Test vertical colorbar with custom label formatting."""
    source = plot.Plot(
        sample_data,
        color_map=ansi.GRAYSCALE,
        render_halfheight=True,
        min_data=0.0,
        max_data=1.0,
    )
    cb = colorbar.colorbar(source, label_fmt="{:.2f}", vertical=True)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_vertical_short():
    """Test vertical colorbar with short height."""
    short_data = [[i for i in range(20)] for _ in range(8)]
    source = plot.Plot(
        short_data,
        color_map=ansi.GRAYSCALE,
        render_halfheight=True,
        min_data=0,
        max_data=10,
    )
    cb = colorbar.colorbar(source, vertical=True)
    cb.show()
    golden.check(cb.as_strings())


if __name__ == "__main__":
    golden.disable_checks()
    sample = gen_norm_data.gen_norm(num_rows=20, num_cols=40, width=0.3, height=0.15, angle=0.5)
    print("Basic:")
    test_colorbar_basic(sample)
    print("Label Fmt:")
    test_colorbar_label_format(sample)
    print("Label Narrow:")
    test_colorbar_narrow()
    print("Infer limits:")
    test_colorbar_infer_limits()
    print("Vertical:")
    test_colorbar_vertical_basic(sample)
    print("Vertical fmt:")
    test_colorbar_vertical_label_format(sample)
    print("Vertical short:")
    test_colorbar_vertical_short()
