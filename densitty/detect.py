"""Utility functions to try to detect terminal/font capabilities"""

from enum import auto, Enum, Flag
from functools import total_ordering
import os
import platform
import sys
from types import MappingProxyType
from typing import Any, Callable, Optional, Sequence
import time

from . import ansi, ascii_art, binning, lineart, truecolor
from . import plot as plotmodule
from .util import FloatLike, ValueRange

if sys.platform == "win32":
    # pylint: disable=import-error
    import ctypes
    from ctypes.windll.kernel32 import GetConsoleMode, GetStdHandle, SetConsoleMode
else:
    # All other platforms should have TERMIOS available
    import fcntl
    import termios

# curses/ncurses isn't always available, so be forgiving if it isn't installed:
curses: Any
try:
    import curses
except ImportError:
    curses = None


@total_ordering
class ColorSupport(Enum):
    """Varieties of terminal color support"""

    NONE = auto()
    ANSI_4BIT = auto()  # i.e. 16 color palette
    ANSI_8BIT = auto()  # i.e. 256 color palette
    ANSI_24BIT = auto()  # i.e. "truecolor" RGB with 8 bits of each

    def __lt__(self, a):
        """Give @total_ordering a comparison, and we can now use <, <=, >, >="""
        if a.__class__ is self.__class__:
            return self.value < a.value
        return NotImplemented


class GlyphSupport(Flag):
    """Varieties of terminal/font glyph rendering support"""

    ASCII = auto()  # Just 7-bit ASCII characters: "- | + _ /"

    BASIC = auto()  # Characters included in DOS/WGL4: "┐ └ ┴ ┬ ├ ┤ ─ ┼ ┘ ┌ │"

    EXTENDED = auto()  # Half-lines, bottom/top horiz lines: "╴ ╵ ╶ ╷ ▁ ▔"

    COMBINING = auto()  # Unicode "Combining Low Line" and "Combining Overline" for "│̲ │̅"


def ansi_get_cursor_pos() -> tuple[int, int]:
    """ANSI codes to read current cursor position"""
    # Write ANSI escape "DSR": Device Status Report. Terminal will respond with position
    sys.stdout.write("\x1b[6n")
    sys.stdout.flush()
    response = ""
    for _ in range(1_000_000):
        response += sys.stdin.read(1)
        # Response should be of the form 'ESC[n;mR' where n and m are row/column
        if response.endswith("R"):
            break
    else:
        raise OSError("No ANSI response from terminal")
    try:
        n_str, m_str = response[2:-1].split(";")
        return (int(m_str), int(n_str))
    except ValueError as e:
        raise OSError from e


if sys.platform == "win32":

    def get_code_response(
        code: str, response_terminator: Optional[str] = None, length: Optional[int] = None
    ) -> str:
        """Windows-based wrapper to avoid control code output to stdout"""
        prev_stdin_mode = ctypes.wintypes.DWORD(0)
        prev_stdout_mode = ctypes.wintypes.DWORD(0)
        GetConsoleMode(GetStdHandle(-10), ctypes.byref(prev_stdin_mode))
        SetConsoleMode(GetStdHandle(-10), 0)
        GetConsoleMode(GetStdHandle(-11), ctypes.byref(prev_stdout_mode))
        SetConsoleMode(GetStdHandle(-11), 7)

        # On Windows, don't try to be non-blocking, just read until terminator
        if length is None:
            length = 1000
        if response_terminator is None:
            response_terminator = "NONE"
        response = ""
        try:
            sys.stdout.write(code)
            sys.stdout.flush()
            for _ in range(length):
                response += sys.stdin.read(1)
                if response[-1] == response_terminator:
                    break
            return response
        finally:
            SetConsoleMode(GetStdHandle(-10), ctypes.byref(prev_stdin_mode))
            SetConsoleMode(GetStdHandle(-11), ctypes.byref(prev_stdout_mode))

else:
    # Not Windows, so use termios/fcntl:

    def get_code_response(
        code: str, response_terminator: Optional[str] = None, length: Optional[int] = None
    ) -> str:
        """Termios-based wrapper to avoid control code output to stdout"""
        timeout_ms = 100
        prev_attr = termios.tcgetattr(sys.stdin)
        attr = prev_attr[:]
        attr[3] = attr[3] & ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, attr)
        stdin_fd = sys.stdin.fileno()
        prev_fl = fcntl.fcntl(stdin_fd, fcntl.F_GETFL)
        fcntl.fcntl(stdin_fd, fcntl.F_SETFL, prev_fl | os.O_NONBLOCK)
        response = ""
        try:
            sys.stdout.write(code)
            sys.stdout.flush()
            for _ in range(timeout_ms):
                response += sys.stdin.read(1)
                if response_terminator and response.endswith(response_terminator):
                    break
                if length and len(response) >= length:
                    break
                time.sleep(0.001)
            else:
                # print(len(response))
                # print(list(response))
                raise OSError("Timeout waiting for terminal response")
            return response

        finally:
            fcntl.fcntl(stdin_fd, fcntl.F_SETFL, prev_fl)
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, prev_attr)


def get_cursor_pos() -> tuple[int, int]:
    """Use the Device Status Report (DSR) sequence to get the current cursor position"""
    response = get_code_response("\033[6n", response_terminator="R")
    try:
        n_str, m_str = response[2:-1].split(";")
        return (int(m_str), int(n_str))
    except ValueError as e:
        raise OSError from e


# Fractional Y axis ticks with a border line will get rendered with Unicode combining characters
# This function will indicate if the terminal will actually attempt to combine characters,
# although a return value of True doesn't necessarily mean that they will be rendered _well_.
def combining_support(debug=False) -> bool:
    """Detect support for combining unicode characters by seeing how far cursor advances when
    we output one. See ucs-detect / blessed projects for more full-featured detection"""
    try:
        start_pos = get_cursor_pos()
        print("│" + lineart.COMBINING_OVERLINE, end="")
        end_pos = get_cursor_pos()
        if start_pos[0] + 1 == end_pos[0]:
            print("\b \b", end="")  # erase the test char we printed
            if debug:
                print(f"From {start_pos} to {end_pos}")
            return True
        print("\b\b  \b\b", end="")  # erase the two characters printed
        if debug:
            print(f"From {start_pos} to {end_pos}")
        return False
    except OSError as e:
        if debug:
            print(f"'combining_support' failed: {e}", file=sys.stderr)
        return False


def screen_version(debug=False) -> tuple[int, int, int]:
    """Use Secondary Device Attributes (DA2) code to find Screen's version triple"""
    try:
        response = get_code_response("\033[>c", response_terminator="c")
        version_str = response.split(";")[1]
        major = int(version_str[0])
        minor = int(version_str[1:3])
        patch = int(version_str[4:])
        return (major, minor, patch)
    except (OSError, ValueError):
        if debug:
            print("Error reading DA2 from 'screen'")
        return (0, 0, 0)


def da1_color_support(debug=False) -> ColorSupport:
    """Read the terminal's DA1 "Device Attributes" and check for color support"""
    try:
        response = get_code_response("\033[c", response_terminator="c")
        response = response.removesuffix("c").removeprefix("\033[?")
        codes = response.split(";")
        if debug:
            print(f"DA1 codes: {codes}")
        # codes[0]: the terminal's architectural class code
        # codes[1:]: the supported extensions, for class codes of 60+ (VT220+)
        # extension "22" is 4b ANSI color, e.g. VT525
        if codes[0].startswith("6") and len(codes) > 1 and "22" in codes[1:]:
            return ColorSupport.ANSI_4BIT
        return ColorSupport.NONE
    except (OSError, ValueError):
        if debug:
            print("Error reading DA1 from terminal")
        return ColorSupport.NONE


def color_support(interactive=True, debug=False) -> ColorSupport:
    """Try to determine the terminal's color support.

    Parameters
    ----------
    interactive : bool
                  Send control codes to terminal if needed to query capability/version.
                  For a sufficiently dumb terminal, this may produce garbage on the screen.
    debug       : bool
                  Output feedback to stdout about the determination logic.
    """

    # This logic around the environment variables mostly parallels that in
    # https://github.com/chalk/supports-color, with various additions.
    # I have not tested this code on all of the various platforms/configurations that it purports
    # to detect. Bug reports and fixes are welcome.

    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    # With tmux/screen, color support must be present in both the multiplexer and the underlying
    # terminal.  So if we see a multiplexer, allow it to set a cap on the allowed colors:
    color_cap = ColorSupport.ANSI_24BIT

    if "FORCE_COLOR" in os.environ:
        if debug:
            print(f"Color detect: found $FORCE_COLOR: '{os.environ['FORCE_COLOR']}'")

        try:
            force_color = min(int(os.environ["FORCE_COLOR"]), 3)
        except ValueError:
            if debug:
                print("  Unexpected value, treating as 0")
            force_color = 0
        force_color_mapping = {
            0: ColorSupport.NONE,
            1: ColorSupport.ANSI_4BIT,
            2: ColorSupport.ANSI_8BIT,
            3: ColorSupport.ANSI_24BIT,
        }
        return force_color_mapping[force_color]

    if "COLORTERM" in os.environ:
        colorterm = os.environ["COLORTERM"]
        if debug:
            print(f"Color detect: found $COLORTERM: '{colorterm}'")
        if "truecolor" in colorterm or "24bit" in colorterm:
            return ColorSupport.ANSI_24BIT
        # My understanding is that S-Lang may also just use this env var to indicate that some
        # color support is available. In that case, we just fall through to the other detection
        # mechanisms below
        if debug:
            print("$COLORTERM not matched, continuing")

    if "TF_BUILD" in os.environ and "AGENT_NAME" in os.environ:
        # Azure DevOps pipelines
        if debug:
            print("Color detect: found $TF_BUILD")
        return ColorSupport.ANSI_4BIT

    if sys.platform == "win32":
        try:
            if debug:
                print("Color detect: from Windows version")
            version = platform.version().split(".")
            maj_version = int(version[0])
            build = int(version[-1])
            if (maj_version, build) < (10, 10586):
                return ColorSupport.ANSI_4BIT
            if (maj_version, build) < (10, 10586):
                return ColorSupport.ANSI_8BIT
            return ColorSupport.ANSI_24BIT
        except ValueError:
            if debug:
                print(f"  Bad platform.version() result: '{platform.version()}'")
                return ColorSupport.ANSI_4BIT

    if "CI" in os.environ:
        if debug:
            print("Color detect: found $CI")
        if any(x in os.environ for x in ["CIRCLECI", "GITEA_ACTIONS", "GITHUB_ACTIONS"]):
            return ColorSupport.ANSI_24BIT
        if any(x in os.environ for x in ["APPVEYOR", "BUILDKITE", "DRONE", "GITLAB_CI"]):
            return ColorSupport.ANSI_4BIT
        return ColorSupport.NONE

    env_term = os.environ.get("TERM", "")
    print(f"$TERM is {env_term}")

    truecolor_terminals = ("truecolor", "xterm-kitty", "xterm-ghostty", "wezterm")
    if env_term in truecolor_terminals:
        if debug:
            print(f"Color detect: from $TERM='{env_term}'")
        return ColorSupport.ANSI_24BIT

    # Note: Gnu Screen and tmux are weird, in that they are sort of the terminal and process
    #       color codes, but the actual color display depends on the terminal that launched them.
    #       So their presence can cap the color support, but not provide it.
    #       Gnu Screen added 256-color support if built appropriately with v4.2 and later, and
    #       optional TrueColor support with v5.0.
    #       Apple's default 'screen' is 4.0 and does not have 256-color support.
    #       'screen' v4.0 can end up with a $TERM like "screen.xterm-256color", even though it
    #       strips/mangles the 256b color codes.
    #       Also iTerm/Terminal's $TERM_PROGRAM will propagate through 'screen'
    if env_term.startswith("screen"):
        version = screen_version() if interactive else (0, 0, 0)
        if version >= (5, 0, 0):
            # This isn't exactly right, since Screen's "truecolor on" / "truecolor off" commands
            # toggle whether it will pass 24bit colors. Not sure how to detect that, though.
            color_cap = ColorSupport.ANSI_24BIT
        elif version >= (4, 2, 0):
            # Ditto: Screen may have been compiled with 256-color support, or not. Assume so.
            color_cap = ColorSupport.ANSI_8BIT
        else:
            color_cap = ColorSupport.ANSI_4BIT
        if debug:
            print(f"GNU Screen detected: capping at {color_cap}")

    if "TERM_PROGRAM" in os.environ:
        term_program = os.environ["TERM_PROGRAM"]
        if debug:
            print(f"Color detect: $TERM_PROGRAM is '{term_program}'")
        if term_program == "iTerm.app":
            if debug:
                print("Color detect: from iTerm version")
            iterm_version = os.environ.get("TERM_PROGRAM_VERSION", "")
            try:
                maj_version = int(iterm_version.split(".")[0])
                if maj_version < 3:
                    return min(ColorSupport.ANSI_8BIT, color_cap)
                return min(ColorSupport.ANSI_24BIT, color_cap)
            except ValueError:
                if debug:
                    print(f"  Bad $TERM_PROGRAM_VERSION: '{iterm_version}'")
        if term_program == "Apple_Terminal":
            if debug:
                print("Color detect: Apple Terminal")
            return ColorSupport.ANSI_8BIT

    if env_term.endswith("-truecolor") or env_term.endswith("-RGB"):
        if debug:
            print("Color detect: $TERM suffix in 24b list")
        return min(ColorSupport.ANSI_24BIT, color_cap)

    if curses:
        if curses.tigetflag("RGB") == 1:
            # ncurses 6.0+ / terminfo added an "RGB" capability to indicate truecolor support
            return min(ColorSupport.ANSI_24BIT, color_cap)

        # Truecolor-supporting terminals will generally report 256 colors in terminfo, so
        # this check is down here after we've given up on finding truecolor support:
        if curses.tigetnum("colors") == 256:
            return min(ColorSupport.ANSI_8BIT, color_cap)

    if env_term.endswith("-256color") or env_term.endswith("-256"):
        if debug:
            print("Color detect: $TERM suffix in 8b list")
        return min(ColorSupport.ANSI_8BIT, color_cap)

    if any(env_term.startswith(x) for x in ("screen", "xterm", "vt100", "vt220", "rxvt")):
        if debug:
            print("Color detect: $TERM prefix in 4b list")
        return ColorSupport.ANSI_4BIT

    if any(x in env_term for x in ("color", "ansi", "cygwin", "linux")):
        if debug:
            print("Color detect: $TERM in 4b list")
        return ColorSupport.ANSI_4BIT

    if interactive:
        if debug:
            print("Color detect: using terminal's Device Attributes")
        return da1_color_support(debug)

    if curses and curses.tigetnum("colors") >= 16:
        return min(ColorSupport.ANSI_4BIT, color_cap)

    return ColorSupport.NONE


GRAYSCALE = MappingProxyType(
    {
        ColorSupport.NONE: ascii_art.EXTENDED,
        ColorSupport.ANSI_4BIT: ascii_art.EXTENDED,
        ColorSupport.ANSI_8BIT: ansi.GRAYSCALE,
        ColorSupport.ANSI_24BIT: truecolor.GRAYSCALE,
    }
)

FADE_IN = MappingProxyType(
    {
        ColorSupport.NONE: ascii_art.EXTENDED,
        ColorSupport.ANSI_4BIT: ansi.FADE_IN_16,
        ColorSupport.ANSI_8BIT: ansi.FADE_IN,
        ColorSupport.ANSI_24BIT: truecolor.FADE_IN,
    }
)


def pick_colormap(maps: dict[ColorSupport, Callable]) -> Callable:
    """Detect color support and pick the best color map"""
    support = color_support()
    return maps[support]


def plot(data, colors=FADE_IN, **plotargs):
    """Wrapper for plot.Plot that picks colormap from dict"""
    colormap = pick_colormap(colors)
    return plotmodule.Plot(data, colormap, **plotargs)


def histplot2d(
    points: Sequence[tuple[FloatLike, FloatLike]],
    bins: (
        int
        | tuple[int, int]
        | Sequence[FloatLike]
        | tuple[Sequence[FloatLike], Sequence[FloatLike]]
    ) = 10,
    ranges: Optional[tuple[Optional[ValueRange], Optional[ValueRange]]] = None,
    align=True,
    drop_outside=True,
    colors=FADE_IN,
    border_line=True,
    fractional_tick_pos=False,
    scale: bool | int = False,
    **plotargs,
    # pylint: disable=too-many-arguments,too-many-positional-arguments
):
    """Wrapper for binning.histogram2d / plot.Plot to simplify 2-D histogram plotting"""
    binned_data, x_axis, y_axis = binning.histogram2d(
        points,
        bins,
        ranges=ranges,
        align=align,
        drop_outside=drop_outside,
        border_line=border_line,
        fractional_tick_pos=fractional_tick_pos,
    )
    p = plot(binned_data, colors, x_axis=x_axis, y_axis=y_axis, **plotargs)
    if scale is True:
        p.upscale()
    elif scale:
        p.upscale(max_expansion=(scale, scale))

    return p
