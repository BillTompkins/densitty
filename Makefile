.PHONY: test

#PY_FILES := $(filter-out %tests.py %gen%.py, $(wildcard *.py))

test:
	PYTHONPATH=. uv run --with numpy,pytest,rich python -m pytest tests/*.py
	PYTHONPATH=. uv run --with numpy,pytest,pytest-cov python -m pytest --cov=densitty tests/*.py

testcov:
	PYTHONPATH=. uv run --with numpy,pytest,pytest-cov python -m pytest --cov=densitty --cov-report=html tests/*.py

lint:
	PYTHONPATH=. uv run --with pylint,rich python -m pylint densitty

format:
	uv run --with black python -m black -l 99 densitty/*.py
	uv run --with black python -m black -l 99 tests/*.py

typecheck:
	PYTHONPATH=. uv run --with mypy,rich python -m mypy densitty
	PYTHONPATH=. uv run --with mypy,numpy,rich python -m mypy tests/numpy_tests.py
	PYTHONPATH=. uv run --with mypy,rich python -m mypy tests/axis_tests.py

colors:
	PYTHONPATH=. uv run --with pytest,rich python tests/color_tests.py
