"""ASCII-art support"""

from typing import Callable, Sequence

from .util import nearest


def color_map(values: Sequence[str]) -> Callable:
    """Returns the closest ascii-art pixel."""

    def compute_pixel_value(frac: float, _=None) -> str:
        return nearest(values, frac)

    return compute_pixel_value


#
# Some example/useful color scales
# Character (glyph) density is dependent on font choice, unfortunately

# Allow the all-caps colormap names:
# pylint: disable=invalid-name
DEFAULT = color_map(" .:-=+*#%@")
EXTENDED = color_map(" .'`^\",:;Il!i>~+?[{1(|/o*#MW&8%B$@")
