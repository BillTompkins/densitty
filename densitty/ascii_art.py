"""ASCII-art support"""

from typing import Callable, Sequence

from .util import quantize


def color_map(values: Sequence[str]) -> Callable:
    """Returns the closest ascii-art pixel."""
    count = len(values)

    def compute_pixel_value(frac: float, _=None) -> str:
        return values[quantize(frac, count)]

    return compute_pixel_value


#
# Some example/useful color scales
# Character (glyph) density is dependent on font choice, unfortunately

# Allow the all-caps colormap names:
# pylint: disable=invalid-name
DEFAULT = color_map(" .:-=+*#%@")
EXTENDED = color_map(" .'`^\",:;Il!i>~+?[{1(|/o*#MW&8%B$@")
