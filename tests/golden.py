import inspect
import os
from pathlib import Path
import sys
import types


def sanitize(a):
    if isinstance(a, str):
        return repr(a)
    if isinstance(a, types.GeneratorType):
        return sanitize(tuple(a))
    if isinstance(a, tuple):
        if len(a) == 1:
            return "(" + sanitize(a[0]) + ",)"
        else:
            return "(" + ", ".join(sanitize(x) for x in a) + ")"
    if isinstance(a, list):
        return "[" + ", ".join(sanitize(x) for x in a) + "]"
    if isinstance(a, float):
        return f"{a:.12}"
    return repr(a)


def check(content, check_name=None):
    content_bytes = sanitize(content).encode("utf-8")

    if check_name is None:
        check_name = inspect.stack()[1].function

    golden_path = Path("tests") / "goldens" / check_name
    try:
        golden_content = golden_path.read_bytes()
    except FileNotFoundError:
        print(f"No golden content for '{check_name}'", file=sys.stderr)
        golden_content = None
    if golden_content is None or golden_content != content_bytes:
        new_golden_path = Path("tests") / "new_goldens" / check_name
        try:
            new_golden_path.write_bytes(content_bytes)
            print(f"Wrote golden content for '{check_name}'", file=sys.stderr)
        except FileNotFoundError:
            pass
    assert golden_content is not None, "No golden output for test"
    assert golden_content == content_bytes, "Mismatch with golden output"
