"""Reading the ``PYREPL_*`` settings.

Every setting is optional, so each accessor here returns a usable default.
Values are read at call time rather than at import time, so that
``override_settings`` works and so that importing this package never requires
configured settings.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from .bindings import Binding, resolve_bindings

__all__ = [
    "get_bindings",
    "get_setup_hooks",
    "get_theme",
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


def get_setup_hooks() -> list[Callable[[], None]]:
    """Return the callables configured by ``PYREPL_SETUP``.

    A single callable, a single dotted path, or a sequence of either is
    accepted, since one hook is the common case and a list is the general one.
    """
    configured = _setting("SETUP", [])
    if configured is None:
        return []
    if callable(configured) or isinstance(configured, str):
        configured = [configured]
    if not isinstance(configured, Sequence):
        raise ImproperlyConfigured(
            "PYREPL_SETUP should be a callable, an import path, or a list of them.",
        )
    hooks = []
    for hook in configured:
        if isinstance(hook, str):
            try:
                hook = import_string(hook)
            except ImportError as error:
                raise ImproperlyConfigured(
                    f"PYREPL_SETUP could not import {hook!r}: {error}",
                ) from error
        if not callable(hook):
            raise ImproperlyConfigured(f"PYREPL_SETUP entry {hook!r} is not callable.")
        hooks.append(hook)
    return hooks
