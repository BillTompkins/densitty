import os
import random
import pytest

mock_terminal_size = os.terminal_size((100, 48))


def mock_get_terminal_size(fd=1):
    return mock_terminal_size


@pytest.fixture()
def set_screensize(monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", mock_get_terminal_size)


@pytest.fixture()
def force_truecolor(monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "3")


@pytest.fixture()
def points():
    """10000 random (x,y) points: x from triangular(-10,10,2), y from gauss(-1,2)"""
    random.seed(1)
    return [(random.triangular(-10, 10, 2), random.gauss(-1, 2)) for _ in range(10000)]
