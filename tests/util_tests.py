import pytest
from fractions import Fraction

from densitty import util


def test_sfrexp10():
    values = (0, 0.01, 0.1, 0.2, 0.99, 1, 1.0, 1.1, 9.99, 10)
    for value in values:
        s, f, e = util.sfrexp10(value)
        assert float(s * f * 10**e) == value
        if value == 0:
            assert f == 0
        else:
            assert 0.1 < f <= 1.0


def test_interp():
    """Test for interp function."""
    assert util.interp([(0, 0, 0), (10, 100, 1000)], 0.5) == (5, 50, 500)
    assert util.interp([(0, 0, 0), (10, 100, 1000)], -0.1) == (0, 0, 0)
    assert util.interp([(0, 0, 0), (10, 100, 1000)], 1.1) == (10, 100, 1000)
