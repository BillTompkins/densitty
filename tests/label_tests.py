import argparse
import itertools
import numpy as np
import pytest
import random
import rich
import sys
from decimal import Decimal as D

from densitty import axis, binning, detect, util
import golden


def gen_labels(value_range: util.ValueRange, num_bins: int):
    print(f"Given [{value_range.min}..{value_range.max}], {num_bins} bins")
    y_labels = axis.gen_full_labels(value_range, num_bins, False, "{}")
    print(f"For Y: {y_labels}")
    x_labels = axis.gen_full_labels(value_range, num_bins, False, "{}")
    print(f"For X: {x_labels}")


def gen_random_axis_values(num):
    bins = random.choices(range(3, 200), k=num)
    lefts = [random.choice((-1, 1)) * 10.0 ** ((random.random() - 0.5) * 20) for _ in range(num)]
    widths = [10.0 ** ((random.random() - 0.5) * 20) for _ in range(num)]
    value_ranges = (
        util.make_value_range((l, l + max(w, l * 1e-10))) for l, w in zip(lefts, widths)
    )

    widths = [10.0**x for x in random.choices(range(-10, 10), k=num)]

    return zip(bins, value_ranges)


# Values for pytest-based tests, with a fixed seed:
random.seed(1)
random_axis_values = tuple(gen_random_axis_values(100))
# For X axis, add a 'tick_space' arg that takes both 0 and 1 values:
random_axis_values_half_spaced = tuple(r + (0,) for r in random_axis_values) + tuple(
    r + (1,) for r in random_axis_values
)


def idfn(arg):
    if isinstance(arg, util.ValueRange):
        return f"({arg.min}-{arg.max})"
    return f"{arg}"


@pytest.mark.parametrize(
    "num_bins,value_range,tick_space", random_axis_values_half_spaced, ids=idfn
)
def test_x_axis(num_bins, value_range, tick_space):
    print(f"{num_bins=} {value_range=} {tick_space=}")
    x_labels = axis.gen_full_labels(value_range, num_bins, True, tick_space, "{}")
    print(f"For X: {x_labels}")
    # For evaluation of failing tests, generate & print an axis with these limits & labels:
    x_axis = axis.Axis(
        value_range,
        labels=x_labels,
        border_line=False,
        values_are_edges=False,
        fractional_tick_pos=True,
    )
    for line in x_axis.render_as_x(num_bins, 4):
        print(line)

    # check the generated labels themselves
    golden_name = f"x_axis_{num_bins}_{value_range.min}_{value_range.max}_{tick_space}"
    golden.check(x_labels, golden_name)


@pytest.mark.parametrize("num_bins,value_range", random_axis_values, ids=idfn)
def test_y_axis(num_bins, value_range):
    print(f"{num_bins=} {value_range=}")
    y_labels = axis.gen_full_labels(value_range, num_bins, False, 0, "{}")
    print(f"For Y: {y_labels}")

    # For evaluation of failing tests, generate & print an axis with these limits & labels:
    y_axis = axis.Axis(
        value_range,
        labels=y_labels,
        border_line=False,
        values_are_edges=False,
        fractional_tick_pos=True,
    )
    for line in y_axis.render_as_y(num_bins, False, False, True):
        print(line)

    # check the generated labels themselves
    golden_name = f"y_axis_{num_bins}_{value_range.min}_{value_range.max}"
    golden.check(y_labels, golden_name)


if __name__ == "__main__":
    from rich import traceback

    traceback.install(show_locals=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--number", "-n", type=int, default=1)
    parser.add_argument("--bins", "-b", type=int, default=None)
    # parser.add_argument("--debug", "-d", action="store_true")
    args = parser.parse_args()

    random.seed(args.seed)

    rand_axis_values = gen_random_axis_values(args.number)

    for num_bins, value_range in rand_axis_value:
        print(f"{num_bins=} {value_range=}")
        gen_labels(value_range, num_bins)

    sys.exit(0)
    # all_labels = axis.gen_full_labels(util.make_value_range((-10, 10)), 40, True, "{}")
    value_range = util.make_value_range((0, 10000))
    for num_rows in range(2, 15):
        labels = axis.gen_full_labels(value_range, num_rows, False, "{}")
        print(f"{labels=}")
        y_axis = axis.Axis(value_range, labels)
        y_printed = y_axis.render_as_y(num_rows, False, False, True)
        for line in y_printed:
            print(line)
    # sys.exit(0)
    value_range = util.make_value_range((10, 10000))
    for num_cols in range(4, 15):
        labels = axis.gen_full_labels(value_range, num_cols, True, "{}")
        print(f"{labels=}")
        x_axis = axis.Axis(value_range, labels)
        x_printed = x_axis.render_as_x(num_cols, 4)
        for line in x_printed:
            print(line)

    print("** Roundness examples")
    for x in (1.0, 2.0, 3.0, 4.0, 5.0, 9.0, 10.0, 1.1, 1.11):
        print(f"roundness({x}): {util.roundness(x)}")
