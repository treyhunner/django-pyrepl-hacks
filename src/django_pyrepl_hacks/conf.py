"""Reading the ``PYREPL_*`` settings.

Every setting is optional, so each accessor here returns a usable default.
Values are read at call time rather than at import time, so that
``override_settings`` works and so that importing this package never requires
configured settings.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from .bindings import Binding, resolve_bindings

__all__ = [
    "get_bindings",
    "get_setup_hook",
    "get_theme",
    "validate_setup",
]


def _setting(name: str, default: object) -> object:
    return getattr(settings, f"PYREPL_{name}", default)


def get_bindings() -> dict[str, Binding]:
    """Return the key bindings to apply, defaults included unless disabled."""
    overrides = _setting("BINDINGS", {})
    if not isinstance(overrides, Mapping):
        raise ImproperlyConfigured("PYREPL_BINDINGS should be a dictionary.")
    use_defaults = bool(_setting("USE_DEFAULT_BINDINGS", True))
    return resolve_bindings(overrides, use_defaults=use_defaults)


def get_theme() -> dict[str, str]:
    """Return syntax highlighting colors to pass to ``update_theme``."""
    theme = _setting("THEME", {})
    if not isinstance(theme, Mapping):
        raise ImproperlyConfigured("PYREPL_THEME should be a dictionary.")
    return dict(theme)


def _not_an_import_path(configured: object) -> ImproperlyConfigured:
    """Return the error for a ``PYREPL_SETUP`` that is not an import path."""
    return ImproperlyConfigured(
        f"PYREPL_SETUP should be an import path string, not {configured!r}.",
    )


def validate_setup() -> None:
    """Check the shape of ``PYREPL_SETUP`` without importing the hook.

    A system check runs during `migrate` and `collectstatic`, so importing the
    hook here would drag REPL-only code into every deploy and fail it if that
    code is not installed there. Whether the path resolves is therefore found
    out when the REPL starts.
    """
    configured = _setting("SETUP", None)
    if configured is not None and not isinstance(configured, str):
        raise _not_an_import_path(configured)


def get_setup_hook() -> Callable[[], None] | None:
    """Return the callable configured by ``PYREPL_SETUP``, if there is one.

    One import path, not a callable and not a list of them. A callable has to
    be imported by settings.py, which every process reads, and this is
    REPL-only code; deferring that import is the whole point of naming it as a
    string. A list would be a second way to say what a hook calling two
    functions already says, in Python, where the order is there to read.
    """
    configured = _setting("SETUP", None)
    if configured is None:
        return None
    if not isinstance(configured, str):
        raise _not_an_import_path(configured)
    try:
        hook: Callable[[], None] = import_string(configured)
    except ImportError as error:
        raise ImproperlyConfigured(
            f"PYREPL_SETUP could not import {configured!r}: {error}",
        ) from error
    if not callable(hook):
        raise ImproperlyConfigured(f"PYREPL_SETUP {configured!r} is not callable.")
    return hook
