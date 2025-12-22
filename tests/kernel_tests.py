import pytest

from densitty import kernel
import golden


def triangle_kernel(dx, dy):
    def tri(d):
        return max(0.0, 1.0 - abs(d))

    return tri(dx) * tri(dy)


def test_kernel2d_basic():
    points = [(0.5, 0.5), (1.0, 0.5)]
    binned = kernel.kernel2d(points, ([0.0, 1.0, 2.0], [0.0, 1.0, 2.0]), kernel=triangle_kernel)
    golden.check(binned)


def test_kernel2d_drop_outside():
    points = [(2.0, 0.5)]
    bins = ([0.0, 1.0, 2.0], [0.0, 1.0])
    included = kernel.kernel2d(points, bins, kernel=triangle_kernel, drop_outside=False)[0]
    excluded = kernel.kernel2d(points, bins, kernel=triangle_kernel, drop_outside=True)[0]
    golden.check((included, excluded))
