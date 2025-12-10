"""Demonstration of the Plot.from_points() convenience method."""

import math
import random

from densitty import plot, truecolor


def demo_simple():
    """Simple example with random points."""
    print("=" * 80)
    print("Simple Example: Random Points")
    print("=" * 80)
    
    random.seed(42)
    points = [(random.random(), random.random()) for _ in range(500)]
    
    # Before: Had to manually bin data
    # from densitty import binning
    # binned, x_range, y_range = binning.bin_pick_num_bins(points, (40, 20))
    # p = plot.Plot(binned, x_axis=Axis(x_range), y_axis=Axis(y_range))
    
    # Now: One simple call
    p = plot.Plot.from_points(points, num_bins=(40, 20))
    p.show()
    print()


def demo_gaussian():
    """Create a 2D Gaussian distribution."""
    print("=" * 80)
    print("Gaussian Distribution")
    print("=" * 80)
    
    random.seed(123)
    points = []
    for _ in range(1000):
        x = random.gauss(0, 0.3)
        y = random.gauss(0, 0.3)
        points.append((x, y))
    
    p = plot.Plot.from_points(
        points,
        num_bins=(50, 25),
        color_map=truecolor.HOT,
    )
    p.show()
    print()


def demo_spiral():
    """Create a spiral pattern."""
    print("=" * 80)
    print("Spiral Pattern")
    print("=" * 80)
    
    points = []
    for i in range(500):
        t = i * 0.1
        r = t * 0.05
        x = r * math.cos(t)
        y = r * math.sin(t)
        points.append((x, y))
    
    p = plot.Plot.from_points(
        points,
        num_bins=(60, 30),
        color_map=truecolor.FADE_IN,
    )
    p.show()
    print()


def demo_sine_wave():
    """Create a sine wave pattern."""
    print("=" * 80)
    print("Sine Wave")
    print("=" * 80)
    
    points = []
    for x in [i / 100 for i in range(-314, 314)]:
        y = math.sin(x)
        # Add some noise
        y += random.gauss(0, 0.1)
        points.append((x, y))
    
    p = plot.Plot.from_points(
        points,
        bin_sizes=(0.2, 0.1),
        color_map=truecolor.BLUE_RED,
    )
    p.show()
    print()


def demo_circle():
    """Create a circle pattern."""
    print("=" * 80)
    print("Circle Pattern")
    print("=" * 80)
    
    points = []
    for i in range(360):
        angle = math.radians(i)
        # Multiple circles with different radii
        for r in [0.3, 0.5, 0.7, 0.9]:
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            points.append((x, y))
    
    p = plot.Plot.from_points(
        points,
        num_bins=(50, 50),
        color_map=truecolor.RAINBOW,
    )
    p.show()
    print()


if __name__ == "__main__":
    demo_simple()
    demo_gaussian()
    demo_spiral()
    demo_sine_wave()
    demo_circle()
