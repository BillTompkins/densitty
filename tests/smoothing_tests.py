import argparse
import pytest
import random
import sys

from densitty import axis, detect, plot, smoothing
import golden


@pytest.fixture
def data():
    """Distribution of points for test"""
    random.seed(1)
    points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", "-s", type=int, default=1)
    parser.add_argument("--num", "-n", type=int, default=100)
    parser.add_argument("--rows", "-r", type=int, default=80)
    parser.add_argument("--cols", "-c", type=int, default=80)
    parser.add_argument("--debug", "-d", action="store_true")
    args = parser.parse_args()

    random.seed(args.seed)
    points = [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(args.num)]

    # x_ctrs = [(x_i / args.cols - 0.5) * 20 for x_i in range(args.cols)]
    # y_ctrs = [(y_i / args.rows - 0.5) * 20 for y_i in range(args.rows)]

    smoothed, x_axis, y_axis = smoothing.smooth2d(
        points, smoothing.triangle(2, 2), bins=(args.rows, args.cols)
    )
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()

    smoothed, x_axis, y_axis = smoothing.smooth2d(
        points, smoothing.gaussian_with_sigma([[2, 0], [0, 2]]), bins=(args.rows, args.cols)
    )
    plot.Plot(smoothed, x_axis=x_axis, y_axis=y_axis).show()

    # detect.histplot2d(points, (args.cols, args.rows), ranges=((x_ctrs[0], x_ctrs[-1]), (y_ctrs[0], y_ctrs[-1]))).show()
    detect.histplot2d(points, (args.cols, args.rows)).show()
