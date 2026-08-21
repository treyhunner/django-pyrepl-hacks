"""A ``shell`` command that prefers the new Python REPL."""

from __future__ import annotations

import types
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError
from django.core.management.commands.shell import Command as BaseShellCommand

from django_pyrepl_hacks import conf, repl
from django_pyrepl_hacks.bindings import describe


class Command(BaseShellCommand):
    """Django's shell command, with ``pyrepl`` as the preferred interface."""

    shells = ["pyrepl", "ipython", "bpython", "python"]  # noqa: RUF012

    def add_arguments(self, parser: Any) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--show-bindings",
            action="store_true",
            help="Print the configured REPL key bindings and exit.",
        )

    def handle(self, **options: Any) -> None:
        if options.get("show_bindings"):
            self.show_bindings()
            return
        super().handle(**options)

    def show_bindings(self) -> None:
        """Write the resolved key bindings to stdout, aligned on the widest key."""
        try:
            bindings = {key: describe(t) for key, t in conf.get_bindings().items()}
        except ImproperlyConfigured as error:
            raise CommandError(str(error)) from error
        if not bindings:
            self.stdout.write("No key bindings are configured.")
            return
        width = max(len(key) for key in bindings)
        for key, description in bindings.items():
            self.stdout.write(f"{key:<{width}}  {description}")

    def pyrepl(self, options: dict[str, Any]) -> None:
        """Run the new Python REPL with Django's namespace and our bindings."""
        usable, reason = repl.can_use_pyrepl()
        if not usable:
            # ImportError is how a shell interface declines, which lets Django
            # move on to the next one in `shells` instead of failing outright.
            raise ImportError(reason or "the new Python REPL is unavailable")

        from _pyrepl.main import interactive_console

        # Past this point an ImportError is a broken configuration rather than
        # an unavailable interface, and silently dropping to the plain shell
        # would hide it. Every one of these is only reachable once the REPL
        # itself has said it can run.
        try:
            repl.setup()
        except ModuleNotFoundError as error:
            if error.name == "pyrepl_hacks":
                raise  # Genuinely absent: decline, and let Django try the rest
            raise CommandError(f"Could not set up the REPL: {error}") from error
        except (ImportError, ImproperlyConfigured, ValueError) as error:
            raise CommandError(f"Could not set up the REPL: {error}") from error

        # A real __main__ module, so that pickling, dataclasses, and anything
        # else that looks up __module__ behaves the way it does in a REPL.
        mainmodule = types.ModuleType("__main__")
        mainmodule.__dict__.update(self.get_namespace(**options))

        interactive_console(
            mainmodule=mainmodule,
            pythonstartup=not options.get("no_startup"),
        )
