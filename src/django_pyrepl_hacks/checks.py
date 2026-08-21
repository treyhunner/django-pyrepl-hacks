"""System checks for the ``PYREPL_*`` settings.

These run on ``manage.py check``, which is the only chance to catch a typo in
a setting before it turns into a traceback in front of the REPL prompt.

Nothing here imports ``pyrepl_hacks``: importing it registers commands, which
builds a REPL reader, which needs a terminal that a check run may not have.
"""

from __future__ import annotations

import sys
from typing import Any

from django.core.checks import Warning
from django.core.exceptions import ImproperlyConfigured

from . import conf, repl
from .bindings import Insert

__all__ = ["check_settings"]


# The token names `_colorize.Syntax` accepts, which is what `update_theme`
# forwards its keyword arguments to.
THEME_TOKENS = frozenset(
    {
        "prompt",
        "keyword",
        "keyword_constant",
        "soft_keyword",
        "builtin",
        "comment",
        "string",
        "number",
        "op",
        "definition",
        "reset",
    },
)


def check_settings(**kwargs: Any) -> list[Any]:
    """Validate every ``PYREPL_*`` setting we understand."""
    return [
        *_check_bindings(),
        *_check_theme(),
        *_check_setup(),
    ]


def _check_bindings() -> list[Any]:
    try:
        bindings = conf.get_bindings()
    except ImproperlyConfigured as error:
        return [_warn(f"PYREPL_BINDINGS is invalid: {error}", "pyrepl_hacks.W002")]
    warnings: list[Warning] = []
    for key, target in bindings.items():
        if not isinstance(target, str | Insert) and not callable(target):
            warnings.append(
                _warn(
                    f"PYREPL_BINDINGS[{key!r}] is {target!r}, which is not a command "
                    "name, an insert(...) value, or a function.",
                    "pyrepl_hacks.W003",
                ),
            )
        elif getattr(target, "__name__", None) == "<lambda>":
            # A command is registered under a name, and a lambda has none.
            warnings.append(
                _warn(
                    f"PYREPL_BINDINGS[{key!r}] is a lambda, which has no name to "
                    "register a command under.",
                    "pyrepl_hacks.W004",
                    hint="Use a def, or insert(...) if you just want to insert text.",
                ),
            )
    return warnings


def _check_theme() -> list[Any]:
    try:
        theme = conf.get_theme()
    except ImproperlyConfigured as error:
        return [_warn(f"PYREPL_THEME is invalid: {error}", "pyrepl_hacks.W005")]
    if theme and sys.version_info < repl.THEME_REQUIRES:
        return [
            _warn(
                "PYREPL_THEME needs Python 3.14 or later, so the shell will "
                "refuse to start with it set.",
                "pyrepl_hacks.W001",
                hint="Remove the setting to use the REPL's own colors.",
            ),
        ]
    unknown = sorted(set(theme) - THEME_TOKENS)
    if not unknown:
        return []
    return [
        _warn(
            f"PYREPL_THEME has unknown token names: {', '.join(unknown)}.",
            "pyrepl_hacks.W006",
            hint=f"Known tokens: {', '.join(sorted(THEME_TOKENS))}.",
        ),
    ]


def _check_setup() -> list[Any]:
    try:
        conf.validate_setup()
    except ImproperlyConfigured as error:
        return [_warn(f"PYREPL_SETUP is invalid: {error}", "pyrepl_hacks.W007")]
    return []


def _warn(message: str, check_id: str, hint: str | None = None) -> Warning:
    """Report a problem without blocking.

    These settings only affect the REPL, and `shell` sets
    `requires_system_checks = []`, so these checks never run for the command
    they describe. An Error here would abort `migrate` and `collectstatic`
    over a key binding, which is the wrong trade every time.
    """
    return Warning(message, hint=hint, id=check_id)
