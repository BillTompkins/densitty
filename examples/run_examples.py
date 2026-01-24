import importlib
import os
import sys

from setup_examples import do_print, separator

sys.path += ["./examples"]

examples = (fname for fname in os.listdir("./examples") if fname.startswith("example_") and fname.endswith(".py"))

for fname in sorted(examples):
    if do_print:
        with open("./examples/" + fname, "r") as f:
            printing = False
            for line in f.readlines():
                if "START" in line:
                    printing = True
                elif printing:
                    print(line, end="")
    # execute the code via an 'import', so that re-importing it won't re-run / re-output anything:
    importlib.import_module(fname[:-3])
