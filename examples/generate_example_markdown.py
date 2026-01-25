#!/usr/bin/env python3

"""Go through examples in order, extract titles & code snippets, add link to screenshot"""

import os
import sys

example_dir = os.path.dirname(os.path.realpath(__file__))
densitty_dir = os.path.dirname(example_dir)
docs_dir = os.path.join(densitty_dir, "docs")

examples = (fname for fname in os.listdir(example_dir) if fname.startswith("example_") and fname.endswith(".py"))


with open(os.path.join(docs_dir, "examples.md"), "wt") as outfile:
    with open(os.path.join(example_dir, "examples.md.header"), "r") as infile:
        for line in infile.readlines():
            outfile.write(line)

    # Process all example files. First line should be a commented title, outputted code text should
    # be preceeded with a line containing the string "START"
    for example in sorted(examples):
        with open(os.path.join(example_dir, example), "r") as infile:
            title = ""
            printing = False
            for line in infile.readlines():
                if not title:
                    title = "#### " + line[1:]  # remove leading '#' from initial comment line
                    outfile.write(title)
                elif "START" in line:
                    printing = True
                    outfile.write("```python\n")
                elif printing:
                    outfile.write(line)
            outfile.write("```\n")
            outfile.write(f"![Plot Output](./examples/{example[:-3]}.png)\n\n")
