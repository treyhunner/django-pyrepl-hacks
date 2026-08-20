"""Tests for the shell management command."""

from contextlib import contextmanager
from io import StringIO
from unittest import TestCase, mock

from django.core.management import CommandError, call_command
from django.test import override_settings

from django_pyrepl_hacks.management.commands.shell import Command


@contextmanager
def running_pyrepl(namespace=None, **patches):
    """Run the pyrepl interface with every REPL-touching piece mocked out.

    Yields the fake ``interactive_console``, which is where the assertions are.
    """
    console = mock.Mock()
    with (
        mock.patch(
            "django_pyrepl_hacks.repl.can_use_pyrepl",
            return_value=(True, ""),
        ),
        mock.patch("django_pyrepl_hacks.repl.load_pyrepl_hacks"),
        mock.patch("django_pyrepl_hacks.repl.setup", **patches),
        mock.patch("_pyrepl.main.interactive_console", console),
        mock.patch.object(Command, "get_namespace", return_value=namespace or {}),
    ):
        yield console


class ShellsTests(TestCase):
    def test_pyrepl_is_preferred(self):
        self.assertEqual(Command.shells[0], "pyrepl")

    def test_djangos_interfaces_are_still_there(self):
        self.assertEqual(Command.shells[1:], ["ipython", "bpython", "python"])


class ShowBindingsTests(TestCase):
    def test_bindings_are_listed(self):
        output = StringIO()
        call_command("shell", show_bindings=True, stdout=output)
        lines = output.getvalue().splitlines()
        self.assertIn("Alt+M      move-to-indentation", lines)
        self.assertIn("Shift+Tab  dedent", lines)

    @override_settings(PYREPL_USE_DEFAULT_BINDINGS=False)
    def test_an_empty_configuration_says_so(self):
        output = StringIO()
        call_command("shell", show_bindings=True, stdout=output)
        self.assertEqual(output.getvalue().strip(), "No key bindings are configured.")


class DjangosOwnBehaviorTests(TestCase):
    def test_running_a_command_still_works(self):
        output = StringIO()
        with mock.patch("sys.stdout", output):
            call_command("shell", command="print(6 * 7)", verbosity=0)
        self.assertEqual(output.getvalue().strip(), "42")


class PyreplInterfaceTests(TestCase):
    def setUp(self):
        self.command = Command()
        self.command.stdout = StringIO()

    def test_an_unusable_repl_declines_the_interface(self):
        with (
            mock.patch(
                "django_pyrepl_hacks.repl.can_use_pyrepl",
                return_value=(False, "tty required"),
            ),
            self.assertRaises(ImportError) as context,
        ):
            self.command.pyrepl({})
        self.assertIn("tty required", str(context.exception))

    def test_the_console_gets_a_main_module_holding_the_namespace(self):
        with running_pyrepl({"User": object}) as console:
            self.command.pyrepl({"no_startup": False})
        mainmodule = console.call_args.kwargs["mainmodule"]
        self.assertEqual(mainmodule.__name__, "__main__")
        self.assertIn("User", mainmodule.__dict__)
        self.assertIs(console.call_args.kwargs["pythonstartup"], True)

    def test_no_startup_is_honored(self):
        with running_pyrepl() as console:
            self.command.pyrepl({"no_startup": True})
        self.assertIs(console.call_args.kwargs["pythonstartup"], False)

    def test_a_broken_setup_is_reported_rather_than_falling_back(self):
        # An ImportError from our own setup used to read as "this interface is
        # unavailable", which quietly dropped the user into the plain shell.
        with (
            running_pyrepl(side_effect=ImportError("nope")),
            self.assertRaises(CommandError) as context,
        ):
            self.command.pyrepl({"no_startup": True})
        self.assertIn("nope", str(context.exception))
