import pytest

from densitty import util


def test_interp():
    """Test for interp function."""
    assert util.interp([(0, 0, 0), (10, 100, 1000)], 0.5) == (5, 50, 500)
    assert util.interp([(0, 0, 0), (10, 100, 1000)], -0.1) == (0, 0, 0)
    assert util.interp([(0, 0, 0), (10, 100, 1000)], 1.1) == (10, 100, 1000)
