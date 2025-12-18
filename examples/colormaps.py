import sys

from densitty import ansi, ascii_art, axis, plot, truecolor

ramp_data = [[x * 0.1 for x in range(200)]]

color_maps = [
    "truecolor.GRAYSCALE",
    "truecolor.GRAYSCALE_LINEAR",
    "ansi.GRAYSCALE",
    "truecolor.BLUE_RED",
    "ansi.BLUE_RED",
    "truecolor.RAINBOW",
    "ansi.RAINBOW",
    "ansi.RAINBOW_16",
    "truecolor.FADE_IN",
    "ansi.FADE_IN",
    "ansi.FADE_IN_16",
    "truecolor.HOT",
    "ansi.HOT",
    "truecolor.COOL",
    "ansi.COOL",
]

color_maps = {
    "RGB maps in truecolor.py": {
        "GRAYSCALE": truecolor.GRAYSCALE,
        "GRAYSCALE_LINEAR": truecolor.GRAYSCALE_LINEAR,  # RGB-interpolated rather than Lab
        "BLUE_RED": truecolor.BLUE_RED,
        "RAINBOW": truecolor.RAINBOW,
        "REV_RAINBOW": truecolor.REV_RAINBOW,
        "FADE_IN": truecolor.FADE_IN,
        "HOT": truecolor.HOT,
        "COOL": truecolor.COOL,
    },
    "256-color maps in ansi.py": {
        "GRAYSCALE": ansi.GRAYSCALE,
        "BLUE_RED": ansi.BLUE_RED,
        "RAINBOW": ansi.RAINBOW,
        "REV_RAINBOW": ansi.REV_RAINBOW,
        "FADE_IN": ansi.FADE_IN,
        "HOT": ansi.HOT,
        "COOL": ansi.COOL,
    },
    "16-color maps in ansi.py": {
        "GRAYSCALE": ansi.GRAYSCALE,
        "BLUE_RED": ansi.BLUE_RED,
        "RAINBOW_16": ansi.RAINBOW_16,
        "REV_RAINBOW_16": ansi.REV_RAINBOW_16,
        "FADE_IN_16": ansi.FADE_IN_16,
    },
    "ASCII-art maps in ascii_art.py": {
        "DEFAULT": ascii_art.DEFAULT,
        "EXTENDED": ascii_art.EXTENDED
    }
}

if __name__ == "__main__":
    x_axis = axis.Axis((0,1), border_line=True)
    for label, maps in color_maps.items():
        print(f"----------{label}----------")
        for name, colormap in maps.items():
            print()
            print(f"{name}:")
            p = plot.Plot(ramp_data, color_map=colormap, x_axis=x_axis, render_halfheight=False)
            p.show()
