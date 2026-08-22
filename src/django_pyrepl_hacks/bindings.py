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
from difflib import get_close_matches

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


def _known_commands() -> set[str] | None:
    """Return the command names the current reader will answer to.

    This is why an unknown command name cannot be a system check: the answer
    only exists once a reader has been built, and building one opens the tty.

    Returns None when there is no reader to ask. By the time bindings are
    applied the shell has already confirmed the REPL can run, so in practice
    that means a test standing in for `pyrepl_hacks`, where the binds go to a
    stub and there is nothing real to validate them against. Declining to
    validate is right there; raising would make this package impossible to
    mock from the outside, which broke a downstream test suite once already.
    """
    try:
        from _pyrepl.simple_interact import _get_reader

        return set(_get_reader().commands)
    except Exception:  # noqa: BLE001
        # Deliberately broad. This is a best-effort probe, and the ways it
        # fails are environment-specific: a RuntimeError from termios with no
        # tty on 3.13, a TypeError out of the import machinery on 3.14 once a
        # test has stood in for part of the module tree. Every one of them
        # means the same thing, and the cost of being wrong is only that a
        # command name goes unvalidated, which is what 0.1.0 did anyway.
        return None


def _check_command_name(keybinding: str, name: str, known: set[str] | None) -> None:
    """Reject a command name the reader does not know.

    `Reader.bind` appends to the keymap without validating, and resolution
    happens at keypress time against `commands.get(...)`, falling back to
    `invalid-command`. So a typo binds cleanly and then the key does nothing
    at all, with nothing ever printed.
    """
    if known is None or name in known:
        return
    message = f"PYREPL_BINDINGS[{keybinding!r}] is {name!r}, which is not a command."
    if suggestions := get_close_matches(name, sorted(known), n=3):
        raise ImproperlyConfigured(
            f"{message} Did you mean {' or '.join(repr(s) for s in suggestions)}?",
        )
    raise ImproperlyConfigured(message)


def apply_bindings(bindings: Mapping[str, Binding]) -> None:
    """Bind every key in ``bindings`` in the current REPL reader."""
    import pyrepl_hacks as repl

    known = _known_commands()
    for keybinding, target in bindings.items():
        try:
            match target:
                case str():
                    _check_command_name(keybinding, target, known)
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
        except ValueError as error:
            # pyrepl-hacks raises this for a key combination it cannot spell,
            # naming the key but not the setting it came from.
            raise ImproperlyConfigured(
                f"PYREPL_BINDINGS[{keybinding!r}] is not a usable key: {error}",
            ) from error


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
