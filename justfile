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
    # Without this a failing run still exits 0, because the exit code is
    # whichever command ran last. That silently disarms `just check`, and
    # everything that depends on it, `just release` included.
    set -euo pipefail
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

# Build the package locally, to inspect the wheel or sdist
build:
    uv sync  # Force uv version error if applicable
    uv build --clear

# Tag the current version and push, which publishes to PyPI via GitHub Actions
release: check
    #!/usr/bin/env bash
    set -euo pipefail
    version="$(uv version --short)"
    branch="$(git branch --show-current)"
    if [ "$branch" != "main" ]; then
        echo "Releases happen from main, but HEAD is on $branch." >&2
        exit 1
    fi
    if [ -n "$(git status --porcelain)" ]; then
        echo "Working tree is dirty. Commit the version bump first." >&2
        exit 1
    fi
    # A release nobody can read the notes for is worth catching while the
    # tag is still the only thing that exists.
    if ! grep -q "^## ${version}\b" CHANGELOG.md; then
        echo "CHANGELOG.md has no '## ${version}' section." >&2
        exit 1
    fi
    if git rev-parse "v${version}" >/dev/null 2>&1; then
        echo "Tag v${version} already exists. Run 'just bump' first." >&2
        exit 1
    fi
    git tag -a "v${version}" -m "Version ${version}"
    git push origin main "v${version}"
    echo "Pushed v${version}. Watch the release run:"
    echo "  https://github.com/treyhunner/django-pyrepl-hacks/actions"

# There is no `publish` recipe: `uv publish` from a laptop needs a token this
# project deliberately does not have, and it would skip the tag/version check
# and the test run that the release workflow does first. Use `just release`.
