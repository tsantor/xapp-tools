set shell := ["bash", "-cu"]
# set shell := ["powershell.exe", "-NoLogo", "-Command"]

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------

python_version := "3.13.1"
aws_profile := "xstudios"
s3_bucket := "xstudios-pypi"

# Dynamic variables (evaluated at runtime - do not edit)
package_name := `uv run python -c "import tomllib; n=tomllib.load(open('pyproject.toml','rb'))['project']['name']; print(n.replace('-', '_'))"`
wheel_name := `ls dist/*.whl 2>/dev/null | head -n 1 | xargs -n 1 basename`
package_url := "https://" + s3_bucket + ".s3.amazonaws.com/" + wheel_name

# DO NOT EDIT BELOW THIS LINE - auto-generated from template
# -----------------------------------------------------------------------------
# Default - list all recipes
# -----------------------------------------------------------------------------

# List all available recipes
[group('help')]
default:
  @just --list

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------

# Create virtual environment (uses `uv`)
[group('environment')]
env:
  uv venv --python {{python_version}}

# Remove virtual environment
[group('environment')]
env-remove:
  rm -rf .venv/

# Recreate environment from scratch
[group('environment')]
env-recreate: env-remove env pip-install-editable

# -----------------------------------------------------------------------------
# Pip
# -----------------------------------------------------------------------------

# Install in editable mode
[group('uv')]
pip-install-editable:
  uv sync --all-groups
  uv pip install -e .

# Add dev dependencies
[group('uv')]
uv-add-dev-dependencies:
  uv add twine wheel build setuptools ruff pipdeptree pre-commit --group dev

# Add test dependencies
[group('uv')]
uv-add-test-dependencies:
  uv add pytest pytest-cov pytest-mock pytest-asyncio coverage --group test

# Run pip list
[group('uv')]
pip-list:
  uv pip list

# Run pip tree
[group('pip')]
pip-tree:
  uv pip tree

# Run pipdeptree
[group('uv')]
pipdeptree:
  uv run pipdeptree

# Sync dependencies from lock file
[group('uv')]
uv-sync:
  uv sync

# Sync dependencies [production, dev, test]
[group('uv')]
uv-install-dev:
  uv sync --no-default-groups --group test --group dev

# Match lock file to current dependencies in pyproject.toml
[group('uv')]
uv-lock:
  uv lock

# Upgrade dependencies and update lock file
[group('uv')]
uv-lock-upgrade:
  uv lock --upgrade

# Check if lock file is up to date
[group('uv')]
uv-lock-check:
  uv lock --check

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

# Run tests
[group('testing')]
pytest:
  uv run pytest -vx --cov --cov-report=html

# Run tests in verbose mode
[group('testing')]
pytest-verbose:
  uv run pytest -vvs --cov --cov-report=html

# Run tests with coverage
[group('testing')]
coverage:
  uv run pytest -q --cov={{package_name}} --cov-report=term-missing --cov-report=html

# Run tests with coverage in verbose mode
[group('testing')]
coverage-verbose:
  uv run pytest -vss --cov={{package_name}} --cov-report=term-missing --cov-report=html

# Run tests with coverage and skip covered
[group('testing')]
coverage-skip:
  uv run pytest -vs --cov={{package_name}} --cov-report=term-missing:skip-covered --cov-report=html

# Open coverage report
[group('testing')]
open-coverage:
  open htmlcov/index.html

# Run tests with coverage threshold gate
[group('testing')]
pytest-cov-gate cov_fail_under="80":
  uv run pytest -q --cov={{package_name}} --cov-report=term-missing --cov-fail-under={{cov_fail_under}}

# Run tox
[group('testing')]
tox:
  uv run tox

# -----------------------------------------------------------------------------
# Linting
# -----------------------------------------------------------------------------

# Run ruff format
[group('linting')]
ruff-format:
  uv run ruff format

# Run ruff check
[group('linting')]
ruff-check:
  uv run ruff check

# Run ruff check with autofix
[group('linting')]
ruff-check-fix:
  uv run ruff check --fix

# Run ruff clean
[group('linting')]
ruff-clean:
  uv run ruff clean

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------

# Remove build artifacts
[group('cleanup')]
clean-build:
  rm -fr build/ dist/ .eggs/
  find . -name '*.egg-info' -o -name '*.egg' -exec rm -fr {} +

# Remove python file artifacts
[group('cleanup')]
clean-pyc:
  find . \( -name '*.pyc' -o -name '*.pyo' -o -name '*~' -o -name '__pycache__' \) -exec rm -fr {} +

# Remove all build and python artifacts
[group('cleanup')]
clean: clean-build clean-pyc

# Clear pytest cache
[group('cleanup')]
clean-pytest-cache:
  rm -rf .pytest_cache

# Clear ruff cache
[group('cleanup')]
clean-ruff-cache:
  rm -rf .ruff_cache

# Clear tox cache
[group('cleanup')]
clean-tox-cache:
  rm -rf .tox

# Clear coverage cache
[group('cleanup')]
clean-coverage:
  rm .coverage
  rm -rf htmlcov

# Clear pytest, ruff, tox, and coverage caches
[group('cleanup')]
clean-tests: clean-pytest-cache clean-ruff-cache clean-tox-cache clean-coverage

# Full cleanup
[group('cleanup')]
clean-all: clean clean-tests

# -----------------------------------------------------------------------------
# Miscellaneous
# -----------------------------------------------------------------------------

# Show directory tree
[group('misc')]
tree:
  tree src -I '__pycache__'

[group('misc')]
tree-root:
  tree -I '.claude|.tmp|.coverage|htmlcov|dist|build|.eggs|*.egg-info|__pycache__|.pytest_cache|.ruff_cache|.tox|.vscode|node_modules|*.csv'

# ----------------------------------------------------------------------------
# Deploy
# -----------------------------------------------------------------------------

# Build source and wheel package
[group('deploy')]
dist: clean
  uv run python3 -m build

# Run full release quality gates
[group('deploy')]
release-check: ruff-check api-check pytest-cov-gate verify-dist wheel-smoke twine-check

# Upload package to pypi test
[group('deploy')]
twine-upload-test: dist
  uv run twine upload dist/* -r pypitest

# Package and upload a release
[group('deploy')]
twine-upload: dist
  uv run twine upload dist/*

# Twine check
[group('deploy')]
twine-check: dist
  uv run twine check dist/*

# Fix twine issues
[group('deploy')]
twine-fix:
  uv pip install -U twine pkginfo

# DO NOT EDIT ABOVE THIS LINE UNLESS YOU KNOW WHAT YOU'RE DOING
# -----------------------------------------------------------------------------
# Project Specific
# -----------------------------------------------------------------------------
