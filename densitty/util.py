"""Utility functions."""

from __future__ import annotations  # for pre-Python 3.12 compatibility

import math
import typing

from bisect import bisect_left
from decimal import Decimal, BasicContext
from fractions import Fraction
from typing import Any, Callable, NamedTuple, Sequence


# FloatLike and Vec are defined in the stubs file util.pyi for type checking
# At runtime, define as Any so older Python versions don't choke:
if not typing.TYPE_CHECKING:
    FloatLike = Any
    Vec = Any


class ValueRange(NamedTuple):
    """Encapsulates a range from min..max"""

    min: Decimal
    max: Decimal


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


def make_decimal(x: FloatLike) -> Decimal:
    """Turn a float into a decimal with reasonable precision,
    avoiding things like 1.0000000000000002220446049250313080847263336181640625"""
    if isinstance(x, Decimal):
        return x
    return BasicContext.create_decimal_from_float(float(x))


def make_value_range(v: ValueRange | Sequence[FloatLike]) -> ValueRange:
    """Produce a ValueRange from from something that may be a sequence of FloatLikes"""
    return ValueRange(make_decimal(v[0]), make_decimal(v[1]))


def partial_first(f: Callable[[FloatLike, FloatLike], FloatLike]) -> Callable:
    """Equivalent to functools.partial, but works with Python 3.10"""

    def out(x: FloatLike):
        return f(x, 0)

    return out


def partial_second(f: Callable[[FloatLike, FloatLike], FloatLike]) -> Callable:
    """Equivalent to functools.partial, but works with Python 3.10"""

    def out(x: FloatLike):
        return f(0, x)

    return out


def sfrexp10(value):
    """Returns sign, base-10 fraction (mantissa), and exponent.
    i.e. (s, f, e) such that value = s * f * 10 ** e.
    if f == 0 => value == 0, else 0.1 < f <= 1.0
    """
    if value == 0:
        return 1, Fraction(0), -100

    if value < 0:
        sign = -1
        value = -value
    else:
        sign = 1

    exp = math.ceil(math.log10(float(value)))
    frac = (Fraction(value) / Fraction(10) ** exp).limit_denominator()
    return sign, frac, exp


round_fractions = (
    Fraction(1, 10),
    Fraction(1, 8),
    Fraction(1, 6),
    Fraction(1, 5),
    Fraction(1, 4),
    Fraction(1, 3),
    Fraction(2, 5),
    Fraction(1, 2),
    Fraction(2, 3),
    Fraction(4, 5),
    Fraction(1, 1),
)


def round_up_ish(value, round_fracs=round_fractions):
    """'Round' the value up to the next highest value in 'round_fracs' times a multiple of 10

    Parameters
    ----------
    value: input value
    round_vals: the allowable values (mantissa in base 10)
    return: the closest round_vals[i] * 10**N equal to or larger than 'value'
    """
    sign, frac_float, exp = sfrexp10(value)

    # if we're passed in a float that can't be represented in binary (say 0.1 or 0.2), it will be
    # rounded up to the next representable float. Adjust to closest sensible fraction:
    frac = Fraction(frac_float).limit_denominator()

    idx = bisect_left(round_fracs, frac)  # find index that this would be inserted before (>= frac)
    round_frac = round_fracs[idx]

    return sign * round_frac * 10**exp


def roundness(value):
    """Metric for how 'round' a value is. 10 is rounder than 1, is rounder than 1.1."""

    if isinstance(value, Sequence):
        # return the average roundness of all elements, with a bonus for the size of the range
        num = len(value)

        if num > 1:
            roundnesses = (roundness(v) for v in value)
            mean = sum(roundnesses) / num
            # give a bonus to sets that cover a longer interval
            log_value_range = math.log(value[-1] - value[0])
        else:
            mean = roundness(value[0])
            log_value_range = -1000  # as if we're covering a range of 10^-1000

        # we want a small bonus to "roundness" if the range is bigger.
        # Keep it small enough that 1..2 won't get expanded to 0.5..2, say
        # log_value_range increases by ~0.3 for every doubling of range
        # which is ~ the penalty for using 1/2 vs 1
        return mean + log_value_range

    # Just a single value, not a sequence:
    if value == 0:
        # 0 is the roundest value
        return 1000  # equivalent to roundness of 1e1000

    if value < 0:
        value = -value

    exp = math.ceil(math.log10(float(value)))
    frac = (Fraction(value) / Fraction(10) ** exp).limit_denominator()
    # so frac is 1 for a multiple of 10, and <1 for non-multiples of 10

    # penalties based on the denominator of 'frac' when expressed as a ratio:
    penalties = {
        1: 0,  # value is power of 10 (1eX)
        2: 0.3,  # value is 5.0eX
        5: 0.5,  # value is 2/4/6/8.0 eX
        10: 1,  # x.1, x.3, x.7, x.9 eX
        4: 1,  # x.25, x.75 eX
        3: 1.2,  # x.333, x.666  TODO: figure out how these are being printed and limit digits
        20: 1.2,  # x.05, x.15, x.35...
        25: 1.8,  # x.04, x.08, ...
        50: 1.8,  # x.02, x.06, ...
        100: 2,  # x.01, ...
    }

    if frac.denominator in penalties:
        return exp - penalties[frac.denominator]

    # In case we have ticks like 1.001, 1.002, 1.003, try to account for number of digits required:
    max_digits = 10
    for digits in range(2, max_digits):
        if 10**digits % frac.denominator == 0:
            return exp - digits

    return exp - max_digits


def roundness_ordered(values):
    """Returns values in order of decreasing roundness"""
    d = {roundness(v): v for v in values}
    for r in reversed(sorted(d)):
        yield d[r]


def most_round(values):
    """Pick the most round of the input values."""
    return next(roundness_ordered(values))
