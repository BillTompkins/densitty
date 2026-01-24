#!/bin/bash

# single argument: the name of the example script (and resulting png)

# Prerequisite: "brew install imagemagick" (into /opt/homebrew/bin)

# This script expects to be run within the main 'densitty' directory, from an iTerm2 terminal window
# - gets the top-level iTerm2 window ID
# - runs the script
# - screen capture of the iTerm2 window
# - uses Imagemagick to remove the window's frame/title, crop down to the actual plot, and add a border

WIN_ID=$(osascript -e 'tell app "iTerm2" to id of window 1')

# get an example name without directory and without ".py" suffix:
EXAMPLE_NAME="$(basename "$1" .py)"

PYTHONPATH=. uv run $1

echo

mkdir -p examples/uncropped
mkdir -p examples/png

screencapture -o -x -l${WIN_ID} examples/uncropped/${EXAMPLE_NAME}.png

# Crop out the right 32 pixels (scrollbar) and top 60 pixels (window title bar).
# Then crop out the bottom 24 pixels to get rid of the rounded window bottom
# Trim to remove all excess border, repage to make the image size the same as the content size
# Crop once more to remove the cursor at the bottom, and trim again.
# Then add a 5-pixel black border around each edge:
/opt/homebrew/bin/magick examples/uncropped/${EXAMPLE_NAME}.png -crop -32+60 -crop +0-24 -trim +repage -crop +0-34 -trim -bordercolor black -border 5 examples/png/${EXAMPLE_NAME}.png
