"""Tests for colorbar generation."""

import pytest

from densitty import ansi, Axis, colorbar, make_colorbar, Plot

import gen_norm_data
import golden


@pytest.fixture
def sample_data():
    """Example data for colorbar tests."""
    return gen_norm_data.gen_norm(num_rows=20, num_cols=40, width=0.3, height=0.15, angle=0.5)


def test_colorbar_basic(sample_data):
    """Test colorbar with typical plot."""
    source = Plot(
        sample_data,
        color_map=ansi.RAINBOW,
        min_data=-50,
        max_data=50,
    )
    cb = make_colorbar(source)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_label_format(sample_data):
    """Test colorbar with custom label formatting."""
    source = Plot(
        sample_data,
        color_map=ansi.GRAYSCALE,
        min_data=0.0,
        max_data=1.0,
    )
    cb = make_colorbar(source, label_fmt="{:.2f}")
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_narrow():
    """Test colorbar with narrow width."""
    narrow_data = [[i for i in range(10)] for _ in range(5)]
    source = Plot(
        narrow_data,
        color_map=ansi.GRAYSCALE,
        min_data=0,
        max_data=10,
    )
    cb = make_colorbar(source)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_infer_limits():
    """Test colorbar when min_data/max_data not set on source plot."""
    data = [[0, 5, 10], [1, 6, 11], [2, 7, 12]]
    source = Plot(
        data,
        color_map=ansi.GRAYSCALE,
    )
    cb = make_colorbar(source)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_vertical_basic(sample_data):
    """Test vertical colorbar."""
    source = Plot(
        sample_data,
        color_map=ansi.FADE_IN,
        min_data=0,
        max_data=100,
    )
    cb = make_colorbar(source, vertical=True)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_vertical_label_format(sample_data):
    """Test vertical colorbar with custom label formatting."""
    source = Plot(
        sample_data,
        color_map=ansi.GRAYSCALE,
        min_data=0.0,
        max_data=1.0,
    )
    cb = make_colorbar(source, label_fmt="{:.2f}", vertical=True)
    cb.show()
    golden.check(cb.as_strings())


def test_colorbar_vertical_short():
    """Test vertical colorbar with short height."""
    short_data = [[i for i in range(20)] for _ in range(8)]
    source = Plot(
        short_data,
        color_map=ansi.GRAYSCALE,
        min_data=0,
        max_data=10,
    )
    cb = make_colorbar(source, vertical=True)
    cb.show()
    golden.check(cb.as_strings())


def test_added_colorbar(sample_data):
    """Test vertical colorbar added to original plot."""
    x_axis = Axis((-10, 10), border_line=True)
    y_axis = Axis((-10, 10), border_line=True)
    source = Plot(
        sample_data,
        min_data=0,
        max_data=1,
        color_map=ansi.FADE_IN,
        x_axis=x_axis,
        y_axis=y_axis,
    )

    colorbar.add_colorbar(source)
    source.show()
    golden.check(source.as_strings())


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

    print("Added bar:")
    test_added_colorbar(sample)
