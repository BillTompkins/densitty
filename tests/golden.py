import inspect
import os
from pathlib import Path
import sys
import types


def check(content, check_name=None):
    if isinstance(content, types.GeneratorType):
        content_str = repr(tuple(content))
    else:
        content_str = repr(content)

    content_bytes = content_str.encode("utf-8")

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
