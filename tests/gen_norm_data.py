import math


def gen_norm(num_rows=48, num_cols=48, width=0.3, height=0.15, angle=0.5):
    transform = [[math.cos(angle), math.sin(angle)], [-math.sin(angle), math.cos(angle)]]

    out = [[0.0 for col in range(num_cols)] for row in range(num_rows)]

    for row in range(num_rows):
        y0 = 2 * (row / (num_rows - 1)) - 1
        for col in range(num_cols):
            x0 = 2 * (col / (num_cols - 1)) - 1
            x = x0 * transform[0][0] + y0 * transform[1][0]
            y = x0 * transform[0][1] + y0 * transform[1][1]
            out[row][col] = math.e ** -(x * x / 2 / width / width + y * y / 2 / height / height)
    return out


"""
norm_data = gen_norm(96, 96)
plot_options = texthist2d.PlotOptions(
    color_map=texthist2d.truecolor.FADE_IN, pixel_type=texthist2d.Pixel.ANSI_HALF_HEIGHT
)
texthist2d.plot(norm_data, plot_options)
"""
