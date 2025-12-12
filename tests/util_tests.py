import pytest

from densitty import util
from densitty.util import ValueRange


def test_interp():
    """Test for interp function."""
    assert util.interp([(0, 0, 0), (10, 100, 1000)], 0.5) == (5, 50, 500)
    assert util.interp([(0, 0, 0), (10, 100, 1000)], -0.1) == (0, 0, 0)
    assert util.interp([(0, 0, 0), (10, 100, 1000)], 1.1) == (10, 100, 1000)


def test_nice_range_basic():
    """Test nice_range expands to nice round boundaries."""
    result = util.nice_range(10, ValueRange(1.5, 9.3))
    assert float(result.min) == 1.0
    assert float(result.max) == 10.0


def test_nice_range_includes_input():
    """Test nice_range always includes the input range."""
    test_cases = [
        (10, ValueRange(1.5, 9.3)),
        (5, ValueRange(0.12, 4.85)),
        (8, ValueRange(-7.5, 2.3)),
        (4, ValueRange(0.0023, 0.0099)),
        (5, ValueRange(1234, 5678)),
    ]
    for num_bins, input_range in test_cases:
        result = util.nice_range(num_bins, input_range)
        assert float(result.min) <= input_range.min, f"Failed for {input_range}"
        assert float(result.max) >= input_range.max, f"Failed for {input_range}"


def test_nice_range_negative():
    """Test nice_range works with negative values."""
    result = util.nice_range(8, ValueRange(-7.5, 2.3))
    assert float(result.min) <= -7.5
    assert float(result.max) >= 2.3


def test_nice_range_small_values():
    """Test nice_range works with small decimal values."""
    result = util.nice_range(4, ValueRange(0.0023, 0.0099))
    assert float(result.min) <= 0.0023
    assert float(result.max) >= 0.0099


def test_nice_range_large_values():
    """Test nice_range works with large values."""
    result = util.nice_range(5, ValueRange(1234, 5678))
    assert float(result.min) <= 1234
    assert float(result.max) >= 5678
