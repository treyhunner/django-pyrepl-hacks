"""Setting up the REPL itself: bindings, theme, and setup hooks.

The ``pyrepl_hacks`` imports live inside the functions here.
Importing it builds a REPL reader, which needs a terminal, so it must not
happen while Django is merely loading apps.
"""

from __future__ import annotations

import sys
from types import ModuleType

from django.core.exceptions import ImproperlyConfigured

from . import conf
from .bindings import apply_bindings

__all__ = ["can_use_pyrepl", "load_pyrepl_hacks", "setup"]


def can_use_pyrepl() -> tuple[bool, str]:
    """Return whether the new REPL can run here, and why not when it cannot.

    ``_pyrepl`` silently falls back to the basic REPL when it cannot run, and
    that fallback drops the namespace we spent all this effort building.
    So the shell command asks first and declines the interface instead.
    """
    try:
        from _pyrepl.main import CAN_USE_PYREPL, FAIL_REASON
    except ImportError as error:
        # `_pyrepl` is private, so a Python that ships without it is one this
        # interface has to decline rather than crash in front of.
        return False, str(error)
    return CAN_USE_PYREPL, FAIL_REASON


def load_pyrepl_hacks() -> ModuleType:
    """Import ``pyrepl_hacks``, translating its failures into ImportError.

    Importing it registers commands, which builds a REPL reader, which needs a
    terminal. A RuntimeError from that is the same kind of "not here, not now"
    answer as an ImportError, and only ImportError makes Django try the next
    interface.
    """
    try:
        import pyrepl_hacks
    except RuntimeError as error:
        raise ImportError(f"pyrepl-hacks could not set up the REPL: {error}") from error
    return pyrepl_hacks


#: Syntax highlighting is themeable from Python 3.14 on, when `_colorize`
#: grew the `Syntax` class that `update_theme` builds a theme out of.
THEME_REQUIRES = (3, 14)


def apply_theme() -> None:
    """Apply ``PYREPL_THEME`` to the REPL's syntax highlighting."""
    theme = conf.get_theme()
    if not theme:
        return
    if sys.version_info < THEME_REQUIRES:
        # Not a mistake, just a Python that cannot honor it, so the REPL comes
        # up unthemed rather than not at all. A project on both versions keeps
        # one settings file, and refusing to start over a color was a worse
        # trade than the missing color, which you can see for yourself anyway.
        # `manage.py check` reports it (W001), including from `runserver`.
        return

    import pyrepl_hacks as repl

    try:
        repl.update_theme(**theme)
    except (AttributeError, TypeError) as error:
        # An unknown color name is an AttributeError on _colorize.ANSIColors,
        # and an unknown token name is a TypeError from Syntax().
        raise ImproperlyConfigured(f"PYREPL_THEME is invalid: {error}") from error


def run_setup_hook() -> None:
    """Call ``PYREPL_SETUP``, if it is set."""
    hook = conf.get_setup_hook()
    if hook is not None:
        hook()


def setup() -> None:
    """Configure the REPL from settings, just before it starts."""
    load_pyrepl_hacks()
    apply_bindings(conf.get_bindings())
    apply_theme()
    run_setup_hook()
