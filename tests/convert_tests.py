import math


def rgb_to_lab(r, g, b):
    """
    Convert RGB color values to CIE L*a*b* color space.

    Args:
        r, g, b: RGB values in range [0, 255]

    Returns:
        tuple: (L*, a*, b*) values where:
               L* is in range [0, 100]
               a* and b* are typically in range [-128, 127]
    """

    # Step 1: Convert RGB to linear RGB (gamma correction)
    def gamma_correct(channel):
        channel = channel / 255.0
        if channel > 0.04045:
            return math.pow((channel + 0.055) / 1.055, 2.4)
        else:
            return channel / 12.92

    r_linear = gamma_correct(r)
    g_linear = gamma_correct(g)
    b_linear = gamma_correct(b)

    # Step 2: Convert linear RGB to XYZ using sRGB matrix
    # Observer is 2° and Illuminant is D65
    x = r_linear * 0.4124564 + g_linear * 0.3575761 + b_linear * 0.1804375
    y = r_linear * 0.2126729 + g_linear * 0.7151522 + b_linear * 0.0721750
    z = r_linear * 0.0193339 + g_linear * 0.1191920 + b_linear * 0.9503041

    # Step 3: Normalize XYZ by reference white point (D65)
    # Reference white point values for D65
    xn = 0.95047
    yn = 1.00000
    zn = 1.08883

    x = x / xn
    y = y / yn
    z = z / zn

    # Step 4: Apply CIE L*a*b* transformation
    def f(t):
        delta = 6.0 / 29.0
        if t > delta**3:
            return math.pow(t, 1.0 / 3.0)
        else:
            return t / (3 * delta**2) + 4.0 / 29.0

    fx = f(x)
    fy = f(y)
    fz = f(z)

    # Calculate L*a*b* values
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    return (L, a, b)


# Example usage and test function
def test_rgb_to_lab():
    """Test the RGB to L*a*b* conversion with some known values."""

    test_cases = [
        ((255, 255, 255), "White"),
        ((0, 0, 0), "Black"),
        ((255, 0, 0), "Red"),
        ((0, 255, 0), "Green"),
        ((0, 0, 255), "Blue"),
        ((128, 128, 128), "Gray"),
    ]

    print("RGB to CIE L*a*b* Conversion Test:")
    print("-" * 50)

    for rgb, color_name in test_cases:
        lab = rgb_to_lab(*rgb)
        print(f"{color_name:6} RGB{rgb} -> L*a*b*({lab[0]:.2f}, {lab[1]:.2f}, {lab[2]:.2f})")


if __name__ == "__main__":
    test_rgb_to_lab()


def lab_to_rgb(L, a, b):
    """
    Convert CIE L*a*b* color values to RGB color space.

    Args:
        L: Lightness value in range [0, 100]
        a: Green-red axis value (typically [-128, 127])
        b: Blue-yellow axis value (typically [-128, 127])

    Returns:
        tuple: (r, g, b) values in range [0, 255], clamped to valid range
    """

    # Step 1: Convert L*a*b* to XYZ
    # Calculate f(Y/Yn) from L*
    fy = (L + 16) / 116

    # Calculate f(X/Xn) and f(Z/Zn) from a* and b*
    fx = a / 500 + fy
    fz = fy - b / 200

    # Apply inverse f function
    def f_inv(t):
        delta = 6.0 / 29.0
        if t > delta:
            return t**3
        else:
            return 3 * delta**2 * (t - 4.0 / 29.0)

    # Convert to normalized XYZ
    x = f_inv(fx)
    y = f_inv(fy)
    z = f_inv(fz)

    # Step 2: Denormalize by reference white point (D65)
    xn = 0.95047
    yn = 1.00000
    zn = 1.08883

    x = x * xn
    y = y * yn
    z = z * zn

    # Step 3: Convert XYZ to linear RGB using inverse sRGB matrix
    r_linear = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g_linear = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b_linear = x * 0.0556434 + y * -0.2040259 + z * 1.0572252

    # Step 4: Apply gamma correction (linear RGB to sRGB)
    def gamma_expand(channel):
        if channel > 0.0031308:
            return 1.055 * math.pow(channel, 1.0 / 2.4) - 0.055
        else:
            return 12.92 * channel

    r_gamma = gamma_expand(r_linear)
    g_gamma = gamma_expand(g_linear)
    b_gamma = gamma_expand(b_linear)

    # Step 5: Convert to 0-255 range and clamp
    def clamp_and_round(value):
        return max(0, min(255, round(value * 255)))

    r = clamp_and_round(r_gamma)
    g = clamp_and_round(g_gamma)
    b = clamp_and_round(b_gamma)

    return (r, g, b)


def test_conversions():
    """Test both RGB->L*a*b* and L*a*b*->RGB conversions."""

    test_colors = [
        (255, 255, 255, "White"),
        (0, 0, 0, "Black"),
        (255, 0, 0, "Red"),
        (0, 255, 0, "Green"),
        (0, 0, 255, "Blue"),
        (128, 128, 128, "Gray"),
        (255, 255, 0, "Yellow"),
        (255, 0, 255, "Magenta"),
        (0, 255, 255, "Cyan"),
    ]

    print("RGB ↔ CIE L*a*b* Round-trip Conversion Test:")
    print("=" * 70)

    for r, g, b, color_name in test_colors:
        # Forward conversion
        lab = rgb_to_lab(r, g, b)

        # Reverse conversion
        rgb_back = lab_to_rgb(*lab)

        # Calculate error
        error = max(abs(r - rgb_back[0]), abs(g - rgb_back[1]), abs(b - rgb_back[2]))

        print(
            f"{color_name:8} RGB({r:3},{g:3},{b:3}) -> "
            f"L*a*b*({lab[0]:6.2f},{lab[1]:6.2f},{lab[2]:6.2f}) -> "
            f"RGB({rgb_back[0]:3},{rgb_back[1]:3},{rgb_back[2]:3}) "
            f"[Error: {error}]"
        )
        assert error == 0


if __name__ == "__main__":
    test_conversions()
