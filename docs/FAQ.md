# FAQ

## Can it be smaller / lighter-weight?
Densitty is designed to be small and does not have external dependencies. The "wheel" is currently only 27KB. But, if you're using it in a very resource-constrained environment, you may want to prune it down. It is designed to be fairly modular, so you shouldn't have to include (say) `binning.py` if you aren't using any binning functionality, or the files `ascii_art.py` & `truecolor.py` if you are only using 256-color output.

If you're doing this, the imports used only for type-checking may require some pruning of the code. If you're taking this approach, please open an issue to let me know that this is an important consideration.

## Why not Matplotlib, or Plotly, or...?
There are several other great options if you want graphical output! However, sometimes you might want in-terminal output for a CLI, or might want to support remote users who might not have X-forwarding set up. Or you are resource-constrained and would rather not include Matplotlib & Numpy in your otherwise small codebase.

## What about other kinds of plots?
There are already several good libraries for in-terminal plotting of other kinds of plots/charts. Check out [Plotext](https://github.com/piccolomo/plotext/), [Termcharts](https://github.com/Abdur-RahmaanJ/termcharts/), [Plotille](https://github.com/tammoippen/plotille), [AsciiChartPy](https://pypi.org/project/asciichartpy/), [TerminalPlot](https://github.com/kressi/terminalplot), with probably more that I've missed.
