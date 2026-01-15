import argparse
import pytest
import random
import sys

from densitty import detect, plot, smoothing
import golden


@pytest.fixture
def data():
    """Distribution of points for test"""
    random.seed(1)
    points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]
    return points


def test_smooth_data_1(data):
    """provide centers"""
    ctrs = tuple(x - 10 for x in range(21))
    smoothed, x_axis, y_axis = smoothing.smooth2d(
        data, smoothing.triangle(2, 2), bins=(ctrs, ctrs)
    )
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()
    golden.check(x_axis, "test_smooth_data_1_x_axis")
    golden.check(y_axis, "test_smooth_data_1_y_axis")
    golden.check(smoothed)


def test_smooth_data_2(data):
    """provide number of centers and ranges"""
    smoothed, x_axis, y_axis = smoothing.smooth2d(
        data, smoothing.triangle(2, 2), bins=(80, 80), ranges=((1, 10), (1, 10))
    )
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()
    golden.check(x_axis, "test_smooth_data_2_x_axis")
    golden.check(y_axis, "test_smooth_data_2_y_axis")
    golden.check(smoothed)


def test_smooth_data_3(data):
    """provide just the number of centers"""
    kernel = smoothing.gaussian_with_inv_cov([[2, 0], [0, 2]])
    smoothed, x_axis, y_axis = smoothing.smooth2d(data, kernel, bins=(80, 80))
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()
    golden.check(x_axis, "test_smooth_data_3_x_axis")
    golden.check(y_axis, "test_smooth_data_3_y_axis")
    golden.check(smoothed)


if __name__ == "__main__":
    from rich import traceback

    traceback.install(show_locals=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--num", "-n", type=int, default=100)
    parser.add_argument("--rows", "-r", type=int, default=80)
    parser.add_argument("--cols", "-c", type=int, default=80)
    parser.add_argument("--smoothness", "-s", type=float, default=3)
    parser.add_argument("--smooth-fraction", "-f", type=float, default=0.5)
    parser.add_argument("--debug", "-d", action="store_true")
    args = parser.parse_args()

    random.seed(args.seed)
    points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(args.num)]

    kernel = smoothing.gaussian_with_inv_cov([[2, 0], [0, 2]])
    smoothed, x_axis, y_axis = smoothing.smooth2d(points, kernel, bins=(80, 80))
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()

    x_ctrs = [(x_i / args.cols - 0.5) * 20 for x_i in range(args.cols)]
    y_ctrs = [(y_i / args.rows - 0.5) * 20 for y_i in range(args.rows)]

    smoothed, x_axis, y_axis = smoothing.smooth2d(
        points, smoothing.triangle(2, 2), bins=(args.rows, args.cols)
    )
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()

    smoothed, x_axis, y_axis = smoothing.smooth2d(
        points, smoothing.gaussian_with_sigmas(0.5, 0.5), bins=(args.rows, args.cols)
    )
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()

    x_width, y_width = smoothing.pick_kernel_bandwidth(
        points,
        bins=(args.rows, args.cols),
        smoothness=args.smoothness,
        smooth_fraction=args.smooth_fraction,
    )
    k = smoothing.gaussian_with_sigmas(x_width, y_width)
    smoothed, x_axis, y_axis = smoothing.smooth2d(
        points, k, bins=(args.rows, args.cols), ranges=((-10, 10), (-10, 10))
    )
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()

    detect.densityplot2d(points).show()

    detect.histplot2d(
        points, (args.cols, args.rows), ranges=((x_ctrs[0], x_ctrs[-1]), (y_ctrs[0], y_ctrs[-1]))
    ).show()
    detect.histplot2d(points, (args.cols, args.rows)).show()
