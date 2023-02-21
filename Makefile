#* Variables
SHELL := /usr/bin/env bash
PYTHON := python
PYTHONPATH := `pwd`

.PHONY: install
install:
	python -m pip install -e .[dev]
	pre-commit install

.PHONY: pre-commit-install
pre-commit-install:
	pre-commit install

.PHONY: format
format:
	pyupgrade --exit-zero-even-if-changed --py37-plus **/*.py
	isort --settings-path pyproject.toml metrico
	black --config pyproject.toml metrico

.PHONY: formatting
formatting: format

.PHONY: test
test:
	pytest -c pyproject.toml tests

.PHONY: coverage
coverage:
	pytest -c pyproject.toml --cov=metrico tests

.PHONY: pylint
pylint:
	pylint --rcfile pyproject.toml metrico/

.PHONY: mypy
mypy:
	mypy --config-file pyproject.toml -p metrico

.PHONY: check-safety
check-safety:
	bandit -r -c pyproject.toml metrico

.PHONY: test-all
test-all: test pylint mypy check-safety

.PHONY: tox
tox:
	tox p
