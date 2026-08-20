# Show available commands
_default:
    @just --list --unsorted

# Install dependencies and prek git hooks
setup:
    # https://github.com/astral-sh/uv/issues/7655#issuecomment-2600986729
    UV_VENV_SEED=1 uv venv
    uv sync --all-groups
    uv run --group dev prek install

# Run prek hooks manually
prek *args:
    uv run --group dev prek run {{ args }}

# Run the tests on both Python versions
test *args:
    #!/usr/bin/env bash
    if [[ -n "{{ args }}" ]]; then
        # Run without coverage
        uv run --python 3.13 --group test python runtests.py {{ args }}
        uv run --python 3.14 --group test python runtests.py {{ args }}
    else
        # Run with coverage
        uv run --python 3.13 --group test coverage run runtests.py
        uv run --python 3.14 --group test coverage run --append runtests.py
        uv run --group test coverage report
    fi

# Run the tests with coverage and open the HTML report
test-html *args:
    uv run --python 3.13 --group test coverage run runtests.py {{ args }}
    uv run --python 3.14 --group test coverage run --append runtests.py {{ args }}
    uv run --group test coverage html
    @echo "Opening coverage report generated at htmlcov/index.html"
    uv run python -m webbrowser htmlcov/index.html

# Lint without changing anything
lint:
    uv run --group lint ruff check
    uv run --group lint ruff format --check
    uv run --group lint rumdl check
    uv run --group typecheck mypy --strict src/django_pyrepl_hacks

# Format code with ruff, markdown with rumdl, and type check
fmt:
    uv run --group lint ruff check --fix
    uv run --group lint ruff format
    uv run --group lint rumdl fmt
    uv run --group typecheck mypy --strict src/django_pyrepl_hacks
    @just prek --all-files

# Run all quality checks, auto-formatting, and run tests
check:
    just fmt
    just test

# Bump version (usage: just bump patch|minor|major)
bump value:
    uv version --bump {{ value }}

# Build the package
build:
    uv sync  # Force uv version error if applicable
    uv build --clear

# Publish to PyPI
publish:
    uv publish
