"""Key bindings for the pyrepl-powered Django shell.

Nothing in this module imports ``pyrepl_hacks`` (and therefore ``_pyrepl``) at
import time.
Settings modules import ``insert`` from this package, and importing a private
stdlib module as a side effect of reading settings would be rude.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured

__all__ = ["DEFAULT_BINDINGS", "Insert", "apply_bindings", "insert", "resolve_bindings"]


@dataclass(frozen=True)
class Insert:
    """A binding that inserts literal text at the cursor."""

    text: str


def insert(text: str) -> Insert:
    """Return a binding that inserts ``text`` at the cursor.

    Meant for use in the ``PYREPL_BINDINGS`` setting:

        PYREPL_BINDINGS = {"Ctrl+N": insert("[2, 1, 3, 4, 7, 11, 18, 29]")}
    """
    return Insert(text)


#: A binding target: a command name, literal text to insert, or a function.
type Binding = str | Insert | Callable[..., None]


DEFAULT_BINDINGS: dict[str, Binding] = {
    "Home": "home",
    "End": "end",
    "Alt+M": "move-to-indentation",
    "Shift+Tab": "dedent",
    "Alt+Down": "move-line-down",
    "Alt+Up": "move-line-up",
    "Ctrl+Up": "previous-history",
    "Ctrl+Down": "next-history",
    "Alt+{": "previous-paragraph",
    "Alt+}": "next-paragraph",
}


def resolve_bindings(
    overrides: Mapping[str, Binding | None] | None = None,
    *,
    use_defaults: bool = True,
) -> dict[str, Binding]:
    """Merge ``overrides`` over ``DEFAULT_BINDINGS``.

    A key mapped to ``None`` is removed, which is how a default binding is
    turned off without turning all of them off.
    """
    bindings: dict[str, Binding | None] = dict(DEFAULT_BINDINGS) if use_defaults else {}
    bindings.update(overrides or {})
    return {key: target for key, target in bindings.items() if target is not None}


def _wants_event(function: Callable[..., None]) -> bool:
    """Return whether ``function`` expects ``(reader, event_name, event)``."""
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return False
    parameters = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    return len(parameters) >= 3


def _command_name(function: Callable[..., None]) -> str:
    """Return the REPL command name for ``function``."""
    name: str | None = getattr(function, "__name__", None)
    if not name or name == "<lambda>":
        raise ImproperlyConfigured(
            "PYREPL_BINDINGS functions need a name: bind a def, not a lambda.",
        )
    return name.replace("_", "-")


def apply_bindings(bindings: Mapping[str, Binding]) -> None:
    """Bind every key in ``bindings`` in the current REPL reader."""
    import pyrepl_hacks as repl

    for keybinding, target in bindings.items():
        match target:
            case str():
                repl.bind(keybinding, target)
            case Insert(text=text):
                repl.bind_to_insert(keybinding, text)
            case _ if callable(target):
                name = _command_name(target)
                repl.register_command(name, with_event=_wants_event(target))(target)
                repl.bind(keybinding, name)
            case _:
                raise ImproperlyConfigured(
                    f"PYREPL_BINDINGS[{keybinding!r}] should be a command name, "
                    f"an insert(...) value, or a function, not {target!r}.",
                )


def describe(target: Binding) -> str:
    """Return a short human-readable description of a binding target."""
    match target:
        case str():
            return target
        case Insert(text=text):
            return f"insert {text!r}"
        case _ if callable(target):
            return _command_name(target)
        case _:  # pragma: no cover - guarded by apply_bindings
            return repr(target)
