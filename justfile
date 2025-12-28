# Development tasks for Tiny Grid

# Install dependencies with all extras
install:
    uv sync --dev --all-extras

# Run all tests
test:
    uv run pytest

# Run tests for a specific file
test-file file:
    uv run pytest {{file}}

# Run a specific test function
test-func func:
    uv run pytest {{func}}

# Run tests with coverage report
test-coverage:
    uv run pytest --cov=tinygrid

# Lint code
lint:
    uv run ruff check .

# Lint and automatically fix issues
lint-fix:
    uv run ruff check --fix --unsafe-fixes .

# Format code
format:
    uv run ruff format .

# Type check with pyright
type-check:
    uv run pyright

# Pre-commit checks: lint fix, format, and type check
pre-commit: lint-fix format type-check
    @echo "Pre-commit checks completed!"

# Run all checks: lint, format, type check, and tests
check: lint format type-check test
    @echo "All checks passed!"

# Build distributions
build:
    uv build

# Publish to PyPI
publish:
    uv publish

# Help - show all available commands
help:
    @just --list
