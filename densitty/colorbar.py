"""Colorbar generation for density plots."""

from .axis import Axis
from .plotting import Plot


def make_colorbar(
    source_plot: Plot,
    label_fmt: str = "{}",
    vertical: bool = False,
) -> Plot:
    """Create a colorbar Plot object from an existing Plot.

    Parameters
    ----------
    source_plot : Plot
        The Plot object to create a colorbar for.
    label_fmt : str
        Format string for min/max labels (e.g., "{:.2f}").
    vertical : bool
        Vertical/Columnnar bar rather than horizontal/row.

    Returns
    -------
    Plot
        A new Plot object representing the colorbar.
    """
    min_value, max_value = source_plot.data_limits()

    color_map = source_plot.color_map

    labels = {
        min_value: label_fmt.format(min_value),
        max_value: label_fmt.format(max_value),
    }
    axis = Axis(
        value_range=(min_value, max_value),
        labels=labels,
        values_are_edges=False,
        border_line=False,
    )

    if vertical:
        size = len(source_plot.data)  # num rows => height
        gradient_data = [[i / (size - 1)] for i in range(size)] if size > 1 else [[0.5]]
    else:
        size = len(source_plot.data[0])  # num cols => width
        gradient_data = (
            [
                [i / (size - 1) for i in range(size)],
            ]
            if size > 1
            else [[0.5]]
        )

    if vertical:
        return Plot(
            data=gradient_data,
            color_map=color_map,
            render_halfheight=source_plot.render_halfheight,
            font_mapping=source_plot.font_mapping,
            y_axis=axis,
            min_data=0,
            max_data=1,
            flip_y=True,
        )

    return Plot(
        data=gradient_data,
        color_map=color_map,
        render_halfheight=source_plot.render_halfheight,
        font_mapping=source_plot.font_mapping,
        x_axis=axis,
        min_data=0,
        max_data=1,
        flip_y=False,
    )


def add_colorbar(source_plot: Plot, label_fmt: str = "{}", padding: str = "  ") -> Plot:
    """Add a vertical colorbar to an existing Plot."""
    cb = make_colorbar(source_plot, label_fmt, vertical=True)
    source_plot.glue_on(cb, padding)
    return source_plot
