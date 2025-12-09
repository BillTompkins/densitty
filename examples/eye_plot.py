import math

from densitty.axis import Axis
from densitty.detect import plot

def eye(num_rows=48, num_cols=48, signal_levels=(-0.75, 0.75)):
    signal_spread_rows = 3
    signal_spread_cols = 3
    signal_weights = {}
    for row in range(signal_spread_rows):
        for col in range(signal_spread_cols):
            val = (1.0 - (row / signal_spread_rows)) * (1.0 - (col / signal_spread_cols))
            signal_weights[(row, col)] = val
            signal_weights[(-row, col)] = val
            signal_weights[(row, -col)] = val
            signal_weights[(-row, -col)] = val

    out = [[0.0 for col in range(num_cols)] for row in range(num_rows)]
    for c in range((num_cols + 1) // 2):
        opposite_c = num_cols - c - 1  # reflected around the center column
        phase = 2 * c / (num_cols - 1)
        frac = (math.cos(phase * math.pi) + 1) / 2
        # print(f"Frac {frac}")
        for start in signal_levels:
            for middle in signal_levels:
                cur_val = start * frac + middle * (1 - frac)
                # print(f"col {c}  {start}->{middle}: {cur_val}")
                signal_row = round((cur_val + 1) / 2 * num_rows)
                for (row_delta, col_delta), weight in signal_weights.items():
                    row = signal_row + row_delta
                    col = c + col_delta
                    if 0 <= row < num_rows and 0 <= col < num_cols:
                        out[row][col] += weight
                    if opposite_c != c:
                        col = opposite_c + col_delta
                        if 0 <= row < num_rows and 0 <= col < num_cols:
                            out[row][col] += weight
    return out


# eye_data = eye(96, 96, signal_levels=(-.75, .75))
eye_data = eye(96, 96, signal_levels=(-0.75, -0.25, 0.25, 0.75))
x_axis = Axis((-1, 1), border_line=True)
y_axis = Axis((-300, 300), border_line=True)
my_plot = plot(eye_data, x_axis=x_axis, y_axis=y_axis)
my_plot.show()
