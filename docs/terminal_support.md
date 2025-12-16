# Color, Size, and Glyph Support - Limitations

## Color Support
*densitty* has colormaps for 24b RGB "Truecolor", 256-color (8b) color palette, 16-color (4b) color pallette, and monochrome ASCII-art. Different terminal emulators (e.g. XTerm, iTerm2, Putty, ...), have different levels of support for these, and sometimes the support can depend on the version, or even the compile options, of the terminal emulator.

Another wrinkle is that users may be using a terminal multiplexer like "tmux" or "screen". These interpret control codes as a terminal emulator does, in order to determine what should go where in a particular pane. And then they send their own control codes to the user's underlying terminal emulator. So it's entirely possible for someone to be running a recent iTerm2 with Truecolor/RGB support, and the Mac's default "screen" build that does _not_ have RGB support.  Conversely, the multiplexer may itself support RGB when the underlying terminal does not, and the multiplexer may translate those RGB colors to the closest 256-color option.

The `color_support()` function in detect.py uses several heuristics to try to determine the level of color support. One useful thing for users to know is its use of the `$FORCE_COLOR` environment variable. That can be set to:

- `FORCE_COLOR=0` for no color support
- `FORCE_COLOR=1` for 16-color
- `FORCE_COLOR=2` for 256-color
- `FORCE_COLOR=3` for RGB

and that will override any other detection heuristics in the code.

If `FORCE_COLOR` is not set, The detection code will examine other environment variables, and optionally try issuing color codes while measuring the cursor movement, to make an educated guess as to the proper level of color support.

## Terminal Size
Python has some built-in code to determine the current terminal size which can be used by the `Plot.upscale()` function to determine the maximum possible output size. If that may fail, you can set the `default_terminal_size` variable in `plot.py` to provide a sensible default for your application. For example:
```python
import os
from densitty import plot

plot.default_terminal_size = os.terminal_size((100, 100))
```
to set a default of 100x100.

# Glyph (character) support
The set of glyphs that can be printed to the user's screen can depend both on their font and on their terminal emulator.
## Main plot area
In the main plot area, typically the lower-half-block character "▄" (U+2584) is used, together with foreground/background coloring, to implement two "pixels". In the unlikely event that it is not available, the `render_halfheight` member of the `Plot` object should be set to false, which will cause the rendering to be done with background-colored " " (space) characters.

## Borders
The ticks for axis labels, and the optional line border for each axis, can use several different sets of characters depending on availability. The character set can be specified in the `Plot.font_mapping` member variable, and several options are specified in `lineart.py`.

- `ascii_font`: Use only ASCII characters like "-", "|", "+", "/", "_"
- `basic_font`: Use additional line art characters that are very widely supported in fonts, like "┘", "┼", ... This is the default.
- `extended_font`: Add some slightly-less-widely supported characters, like "▁", "▔", "╴", "╶", "╵", "╷".

### Fractional ticks
A challenge when adding tick marks on X and Y axes is that you can't always put a tick at the desired position. With 2-d histograms, the tick marks would typically go on a bin boundary, but on the X axis, there aren't widely supported glyphs for a tick "between" two characters. On the Y axis, we can use "-" for the boundary between the top and bottom pixels. We could use "\_" for the boundary with the next lower character, but combining "\_" with a vertical border line is tricky. For a non-histogram plot, where integral values are on the pixel centers, the X axis is straightforward (we can use "|"), but the Y axis doesn't work well.

#### X Axis
If the X axis' `fractional_tick_pos` is set, the characters "╱╲" will be used to indicate a tick mark "between" two characters. On the extreme of the axis, that will be "│╲" or "╱│" to match the other border line.

#### Y Axis
If the Y axis' `fractional_tick_pos` is set without a border line, the "▔" and "▁" characters will be used for ticks at or near the boundary with the next higher or lower character. If using `basic_font` or `ascii_font`, those will be translated into "/" and "\_".
If the Y axis `border_line` is set, however, the unicode "Combining Low Line" (U+0332) and "Combining Over Line" (U+0305) are used together with the vertical bar "│" as an attempt to have both the high/low tick mark and the border line.
This "combining Unicode" support is very terminal-emulator dependent. Unfortunately, some terminals shift the horizontal position of the vertical line when combining it. I likely wouldn't use it unless I knew that the user was using a particular terminal emulator where it looks ok.
