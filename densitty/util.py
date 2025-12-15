"""Utility functions."""

from bisect import bisect_left
from collections import namedtuple
from decimal import Decimal
import math
from typing import Any, Protocol, Sequence, SupportsFloat


class FloatLike[T](SupportsFloat, Protocol):
    """A Protocol that supports the arithmetic ops we require, and can convert to float"""

    def __lt__(self, __other: T) -> bool: ...
    def __add__(self, __other: Any) -> T: ...
    def __sub__(self, __other: Any) -> T: ...
    def __mul__(self, __other: Any) -> T: ...
    def __truediv__(self, __other: Any) -> T: ...
    def __abs__(self) -> T: ...


ValueRange = namedtuple("ValueRange", ["min", "max"])

type Vec = Sequence[FloatLike]


def clamp(x, min_x, max_x):
    """Returns the value if within min/max range, else the range boundary."""
    return max(min_x, min(max_x, x))


def clamp_rgb(rgb):
    """Returns closest valid RGB value"""
    return tuple(clamp(round(x), 0, 255) for x in rgb)


def interp(piecewise: Sequence[Vec], x: float) -> Vec:
    """Evaluate a piecewise linear function, i.e. interpolate between the two closest values.
    Parameters
    ----------
    piecewise: Sequence[Vec]
               Evenly spaced function values. piecewise[0] := f(0.0), piecewise[-1] := f(1.0)
    x:         float
               value between 0.0 and 1.0
    returns:   Vec
               f(x)
    """
    max_idx = len(piecewise) - 1
    float_idx = x * max_idx
    lower_idx = math.floor(float_idx)

    if lower_idx < 0:
        return piecewise[0]
    if lower_idx + 1 > max_idx:
        return piecewise[-1]
    frac = float_idx - lower_idx
    lower_vec = piecewise[lower_idx]
    upper_vec = piecewise[lower_idx + 1]
    return tuple(lower * (1.0 - frac) + upper * frac for lower, upper in zip(lower_vec, upper_vec))


def nearest(stepwise: Sequence, x: float):
    """Given a list of function values, return the value closest to the specified point
    Parameters
    ----------
    stepwise: Sequence[Any]
              Evenly spaced function values. piecewise[0] := f(0.0), piecewise[-1] := f(1.0)
    x:        float
              value between 0.0 and 1.0
    returns:  Any
              f(x') for x' closest to x in the original sequence
    """
    max_idx = len(stepwise) - 1
    idx = round(x * max_idx)

    clamped_idx = clamp(idx, 0, max_idx)
    return stepwise[clamped_idx]


def decimal_value_range(v: ValueRange | Sequence):
    """Produce a ValueRange containing Decimal values"""
    return ValueRange(Decimal(v[0]), Decimal(v[1]))


def sfrexp10(value):
    """Returns sign, base-10 fraction (mantissa), and exponent.
    i.e. (s, f, e) such that value = s * f * 10 ** e with 0 <= f < 1.0
    """
    if value == 0:
        return 1, 0, -100

    sign = -1 if value < 0 else 1

    v = Decimal(abs(value))
    exponent = v.adjusted() + 1
    frac = v.scaleb(-exponent)  # scale frac's exponent to be 0

    return sign, frac, exponent


round_fractions = (
    Decimal(1) / Decimal(10),
    Decimal(1) / Decimal(8),
    Decimal(1) / Decimal(6),
    Decimal(1) / Decimal(5),
    Decimal(1) / Decimal(4),
    Decimal(1) / Decimal(3),
    Decimal(2) / Decimal(5),
    Decimal(1) / Decimal(2),
    Decimal(2) / Decimal(3),
    Decimal(4) / Decimal(5),
    Decimal(1),
)


def round_up_ish(value, round_fracs=round_fractions):
    """'Round' the value up to the next highest value in 'round_vals' times a multiple of 10

    Parameters
    ----------
    value: input value
    round_vals: the allowable values (mantissa in base 10)
    return: the closest round_vals[i] * 10**N equal to or larger than 'value'
    """
    sign, frac, exp = sfrexp10(value)

    # if we're passed in a float that can't be represented in binary (say 0.1 or 0.2), it will be
    # rounded up to the next representable float. Subtract the smallest possible value (ulp) to
    # so that when we round up, it can match an exact Decimal("0.1") or such:
    frac -= Decimal(math.ulp(frac))

    idx = bisect_left(round_fracs, frac)  # find index that this would be inserted before (>= frac)
    round_frac = round_fracs[idx]

    return sign * round_frac.scaleb(exp)


def roundness(value):
    """Metric for how 'round' a value is. 10 is rounder than 1, is rounder than 1.1."""

    # if value is a sequence, combine the roundness of all elements, prioritizing in order:
    if isinstance(value, Sequence):
        out, weight = 0, 1
        for v in value:
            out += roundness(v) * weight
            weight *= 0.99
        return out

    if value == 0:
        # 0 is the roundest value
        return 1000  # equivalent to roundness of 1e1000
    _, frac, exp = sfrexp10(value)

    round_frac = round(frac, 5)  # round to specific # of digits so we can interpret as fraction
    penalties = {
        1.00000: 0.0,  # no penalty for multiples of 10
        0.50000: 0.5,  # penalty for multiple of 5 vs multiple of 10
        0.25000: 0.6,  # penalty for multiple of 4 vs multiple of 10
        0.75000: 0.6,  #
        Decimal("0.33333"): 0.7,  # penalty for multiple of 3 vs multiple of 10
        Decimal("0.66667"): 0.7,  #
        0.12500: 0.8,  # penalty for multiple of 8 vs multiple of 10
        0.37500: 0.8,
        0.62500: 0.8,
        0.87500: 0.8,
    }

    if round_frac in penalties:
        return exp - penalties[round_frac]

    # Ouch: our fractional part is just not nice, so maximally un-round:
    return -1000  # equivalent to roundness of 1e-1000


def most_round(values):
    """Pick the most round of the input values. Ties go to the earliest."""
    best_r = -1e100
    best_v = 0
    for v in values:
        r = roundness(v)
        if r > best_r:
            best_r, best_v = r, v
    return best_v


def pick_step_size(value_range, num_steps_hint, min_steps_per_label=1) -> tuple[Decimal, Decimal]:
    """Try to pick a step size that gives nice round values for step positions.
    For coming up with nice tick positions for an axis, and with nice bin sizes for binning.
    For an axis, it is also useful to produce an interval between labeled ticks.

    Parameters
    ----------
    value_range: bounds of interval
    num_steps_hint: approximate number of steps desired for the interval
    min_steps_per_label: for use with axis/label generation, as labels take more space than ticks
    return: step size, interval between labeled steps/ticks
    """
    num_steps_hint = max(1, num_steps_hint)
    # if steps are 0,1,2,3,4,5,6... or 0,2,4,6,8,10,... steps_per_label of 5 is sensible,
    # if steps are 0,5,10,15,20,... steps_per_label of 4 is sensible
    nominal_step = (value_range.max - value_range.min) / num_steps_hint

    # Figure out the order-of-magnitude (power of 10), aka "decade" of the steps:
    log_nominal = math.log10(nominal_step)
    log_decade = math.floor(log_nominal)  # i.e. # of digits
    decade = Decimal(10) ** log_decade

    # Now figure out where in that decade we are, so we can pick the closest 1/2/5 value
    log_frac = log_nominal - log_decade  # remainder after decade taken out
    frac = 10**log_frac  # i.e. fraction through the decade (shift decimal point to front)

    # common-case: label every or every-other, or every 5th, or every 10th
    if min_steps_per_label <= 2:
        steps_per_label = min_steps_per_label
    elif min_steps_per_label <= 5:
        steps_per_label = 5
    else:
        steps_per_label = max(min_steps_per_label, 10)

    if frac < 1.1:
        step = decade
    elif frac < 2.2:
        step = 2 * decade
        # Steps of .2, don't label every other one
        if steps_per_label == 2:
            steps_per_label = 5
    elif frac < 5.5:
        step = 5 * decade
        # ticks every .5, don't label every 5th
        if steps_per_label == 5:
            steps_per_label = max(round(min_steps_per_label / 2) * 2, 6)
    else:
        step = 10 * decade

    return step, step * steps_per_label
