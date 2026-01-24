import random

import sys

# Note: for reproducibility, always use the same random seed for generated data:
random.seed(1)

separator = "\n\n" + "=" * 80

do_print = "--quiet" not in sys.argv
