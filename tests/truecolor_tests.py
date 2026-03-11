from densitty.truecolor import RGB, interp


def test_interp():
    """Test for interp function."""
    assert interp([RGB((0, 0, 0)), RGB((10, 100, 1000))], 0.5) == RGB((5, 50, 500))
    assert interp([RGB((0, 0, 0)), RGB((10, 100, 1000))], -0.1) == RGB((0, 0, 0))
    assert interp([RGB((0, 0, 0)), RGB((10, 100, 1000))], 1.1) == RGB((10, 100, 1000))
