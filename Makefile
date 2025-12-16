.PHONY: test
test:
	PYTHONPATH=. uv run --with numpy,pytest,readchar,rich python -m pytest tests/*.py
	PYTHONPATH=. uv run --with numpy,pytest,readchar,pytest-cov python -m pytest --cov=densitty tests/*.py

.PHONY: testcov
testcov:
	PYTHONPATH=. uv run --with numpy,pytest,pytest-cov,readchar python -m pytest --cov=densitty --cov-report=html tests/*.py

.PHONY: golden-accept
golden-accept:
	PYTHONPATH=. uv run --with readchar python tests/golden_diff.py

.PHONY: lint
lint:
	PYTHONPATH=. uv run --with pylint,rich python -m pylint densitty

.PHONY: format
format:
	uv run --with black python -m black -l 99 densitty/*.py
	uv run --with black python -m black -l 99 tests/*.py

.PHONY: typecheck
typecheck:
	PYTHONPATH=. uv run --with mypy,rich python -m mypy densitty
	PYTHONPATH=. uv run --with mypy,numpy,rich python -m mypy tests/numpy_tests.py
	PYTHONPATH=. uv run --with mypy,rich python -m mypy tests/axis_tests.py

.PHONY: colors
colors:
	PYTHONPATH=. uv run --with pytest,rich python tests/color_tests.py

.PHONY: build
build: ## Build wheel file
	rm -rf ./dist
	uvx --from build pyproject-build --installer uv

.PHONY: tag
tag: ## Add a Git tag and push it to origin with syntax: make tag TAG=tag_name
ifeq ($(origin TAG),undefined)
	$(error "ERROR: use like 'make tag TAG=tag_name'")
else
	@echo "Creating git tag: ${TAG}"
	git tag -a ${TAG} -m ""
	@echo "Pushing tag to origin: ${TAG}"
	git push origin ${TAG}
endif

.PHONY: publish-test
publish-test: build
	@echo "Publishing to testpypi"
	uvx twine upload --repository testpypi dist/*

.PHONY: publish
publish: build
	@echo "Publishing to REAL pypi"
	uvx twine upload dist/*
