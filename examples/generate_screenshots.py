#!/usr/bin/env python3

"""Create a new window in iTerm2, run the python snippet, screenshot that window, exit"""

# NOTE: Must enable iTerm2's Python API from Settings:General:Magic
#       Also: create a 'screenshot' profile with the desired window size.
# assumes 'densitty' is checked out in a directory of the same name within the user's home dir

import AppKit
import asyncio
import iterm2
import os
import sys

example_dir = os.path.dirname(os.path.realpath(__file__))
densitty_dir = os.path.dirname(example_dir)
screenshot_prog = os.path.join(example_dir, "screenshot_example.sh")

examples = (fname for fname in os.listdir(example_dir) if fname.startswith("example_") and fname.endswith(".py"))

# Launch the app
AppKit.NSWorkspace.sharedWorkspace().launchApplication_("iTerm2")

async def main(connection):
    app = await iterm2.async_get_app(connection)

    # Foreground the app
    await app.async_activate()

    for example in sorted(examples):
        example_path = os.path.join(example_dir, example)
        cmd = f"/bin/bash -l -c 'cd {densitty_dir}; {screenshot_prog} {example_path}; sleep 5'"
        await iterm2.Window.async_create(connection, profile="screenshot", command=cmd)
        await asyncio.sleep(8)

iterm2.run_until_complete(main, False)
