import argparse
import numpy as np
import pytest
import sys

from densitty import axis, binning, detect
import golden


@pytest.fixture
def data():
    """values from 1.0 (inclusive) to 10.0 (exclusive)"""
    out = []
    for x in np.arange(1.0, 10.0, 0.25):
        for y in np.arange(1.0, 10.0, 0.25):
            out += [(x, y)]
    return out


@pytest.fixture
def data_to_edge():
    """values from 1.0 (inclusive) to 10.0 (inclusive)"""
    out = []
    for x in np.arange(1.0, 10.25, 0.25):
        for y in np.arange(1.0, 10.25, 0.25):
            out += [(x, y)]
    return out


def test_binning_drop_data():
    points = [(x, 1) for x in np.arange(-1.0, 11.0, 0.25)]
    binned = binning.bin_edges(points, (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), (0, 1, 2))
    golden.check(binned)


def test_binning_no_drop_data():
    points = [(x, 1) for x in np.arange(-1.0, 11.0, 0.25)]
    binned = binning.bin_edges(
        points, (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), (0, 1, 2), drop_outside=False
    )
    golden.check(binned)


def test_binning_auto_case_1(data):
    binned = binning.bin_pick_num_bins(data, (9, 9))
    golden.check(binned)


def test_binning_auto_case_2(data):
    # data is from [1.0..10.0), so 9 natural bins. Suggest 10 instead, and bin_pick_num_bins
    # should still return 9x9 with ranges of (1..10)
    binned = binning.bin_pick_num_bins(data, (10, 10))
    golden.check(binned)


def test_binning_auto_spec_range_1(data):
    # Tell it the data is ranging from 0..10, and we should get 10x10 bins back
    binned = binning.bin_pick_num_bins(data, (10, 10), ((0, 10), (0, 10)))
    golden.check(binned)


def test_binning_fixed_1(data):
    """no auto-adjust, with 45x9 bins, from 1..10"""
    binned = binning.bin_pick_num_bins(data, (36, 9), ((1, 10), (1, 10)), auto_adjust_bins=False)
    golden.check(binned)


def test_binning_fixed_2(data):
    """no auto-adjust, with 45 bins, from 1..9.75(implicit)"""
    binned = binning.bin_pick_num_bins(data, (36, 9), auto_adjust_bins=False)
    golden.check(binned)


def test_binning_edge_1(data_to_edge):
    """auto-adjust, with suggested 45x9 bins"""
    binned = binning.bin_pick_num_bins(data_to_edge, (36, 9))
    golden.check(binned)


def test_binning_edge_2(data_to_edge):
    """no auto-adjust, with 45x9 bins, from 1..10. Last bin will get extra counts."""
    binned = binning.bin_pick_num_bins(
        data_to_edge, (36, 9), ((1, 10), (1, 10)), auto_adjust_bins=False
    )
    golden.check(binned)


def test_empty_data():
    """pass in blank data"""
    binned = binning.bin_pick_num_bins([], (5, 5))
    golden.check(binned)


def test_single_data():
    """pass in single data point"""
    binned = binning.bin_pick_num_bins([(1, 1)], (5, 5))
    golden.check(binned)


def test_single_valued_data():
    """pass in single data point"""
    binned = binning.bin_pick_num_bins([(1, 1), (1, 2)], (5, 5))
    golden.check(binned)


def test_bin_data_1(data):
    """provide bin sizes"""
    binned = binning.bin_data(data, (1, 1), ((1, 10), (1, 10)))
    golden.check(binned)


def test_bin_data_2(data):
    """provide bin sizes, use calculated data min/max"""
    binned = binning.bin_data(data, (1, 1))
    print(binned[1:])
    golden.check(binned)


def test_bin_data_unaligned(data):
    """Don't require bin edges to be aligned"""
    binned = binning.bin_data(data, (1, 1), ((0.5, 10), (0.5, 10)), align_bins=False)
    golden.check(binned)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", "-s", type=int, default=1)
    parser.add_argument("--num", "-n", type=int, default=1000)
    parser.add_argument("--bins", "-b", type=int, default=80)
    parser.add_argument("--debug", "-d", action="store_true")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    points = rng.random((args.num, 2))
    binned, x_range, y_range = binning.bin_pick_num_bins(points, (args.bins, args.bins))
    # binned, x_range, y_range = binning.bin_pick_num_bins(points, (80,80), ranges=((0,1), (0,1)), auto_adjust_bins=False)
    if args.debug:
        print(f"X range: {x_range.min}, {x_range.max}")
        print(f"Y range: {y_range.min}, {y_range.max}")
        print(f"Binned data size: {len(binned[0])}x{len(binned)}")
    x_axis = axis.Axis(x_range, values_are_edges=True, border_line=True)
    y_axis = axis.Axis(y_range, values_are_edges=True, border_line=True)
    detect.plot(binned, x_axis=x_axis, y_axis=y_axis).show()

    binned, x_range, y_range = binning.bin_data(
        points, (0.1, 0.1), ((0, 1), (0, 1)), align_bins=True, drop_outside=True
    )
    x_axis = axis.Axis(x_range, values_are_edges=True, border_line=True)
    y_axis = axis.Axis(y_range, values_are_edges=True, border_line=True)
    histplot = detect.plot(binned, x_axis=x_axis, y_axis=y_axis)
    histplot.show()
    histplot.upscale().show()
