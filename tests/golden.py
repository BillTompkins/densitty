import inspect
import os
from pathlib import Path
import sys
import types


def check(content, check_name=None):
    if isinstance(content, types.GeneratorType):
        content_str = str(tuple(content))
    else:
        content_str = str(content)

    if check_name is None:
        check_name = inspect.stack()[1].function

    golden_path = Path("tests") / "goldens" / check_name
    try:
        golden_content = golden_path.read_text()
    except FileNotFoundError:
        print(f"No golden content for '{check_name}'", file=sys.stderr)
        golden_content = None
    if golden_content is None or golden_content != content_str:
        new_golden_path = Path("tests") / "new_goldens" / check_name
        try:
            new_golden_path.write_text(content_str)
            print(f"Wrote golden content for '{check_name}'", file=sys.stderr)
        except FileNotFoundError:
            pass
    assert golden_content is not None, "No golden output for test"
    assert golden_content == content_str, "Mismatch with golden output"
