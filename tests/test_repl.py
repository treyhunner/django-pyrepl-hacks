"""Tests for configuring the REPL just before it starts."""

from unittest import TestCase, mock

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_pyrepl_hacks import repl
from django_pyrepl_hacks.bindings import DEFAULT_BINDINGS


def a_hook():
    """The hook PYREPL_SETUP points at below, patched to watch it run."""


class SetupTests(TestCase):
    def setUp(self):
        self.repl_hacks = mock.Mock()
        patcher = mock.patch.dict("sys.modules", {"pyrepl_hacks": self.repl_hacks})
        patcher.start()
        self.addCleanup(patcher.stop)
        known = mock.patch(
            "django_pyrepl_hacks.bindings._known_commands",
            return_value=set(DEFAULT_BINDINGS.values()),
        )
        known.start()
        self.addCleanup(known.stop)

    def test_default_bindings_are_applied(self):
        repl.setup()
        self.repl_hacks.bind.assert_any_call("Alt+M", "move-to-indentation")

    def test_theme_is_left_alone_when_unset(self):
        repl.setup()
        self.repl_hacks.update_theme.assert_not_called()

    @override_settings(PYREPL_THEME={"string": "red"})
    def test_theme_is_applied(self):
        with mock.patch.object(repl, "THEME_REQUIRES", (3, 13)):
            repl.setup()
        self.repl_hacks.update_theme.assert_called_once_with(string="red")

    @override_settings(PYREPL_THEME={"nonsense": "red"})
    def test_an_unknown_theme_token_is_reported(self):
        self.repl_hacks.update_theme.side_effect = TypeError("nonsense")
        with (
            mock.patch.object(repl, "THEME_REQUIRES", (3, 13)),
            self.assertRaises(ImproperlyConfigured) as context,
        ):
            repl.setup()
        self.assertIn("PYREPL_THEME is invalid", str(context.exception))

    @override_settings(PYREPL_THEME={"string": "red"})
    def test_a_theme_on_too_old_a_python_is_skipped_rather_than_fatal(self):
        """One settings file has to serve a team spread across both versions.

        Refusing to start meant a teammate on 3.13 had no shell at all because
        someone on 3.14 wanted colors. `manage.py check` reports it instead.
        """
        with mock.patch.object(repl, "THEME_REQUIRES", (99, 0)):
            repl.setup()
        self.repl_hacks.update_theme.assert_not_called()

    @override_settings(PYREPL_SETUP="tests.test_repl.a_hook")
    def test_the_setup_hook_is_called(self):
        with mock.patch("tests.test_repl.a_hook") as hook:
            repl.setup()
        hook.assert_called_once_with()


class LoadPyreplHacksTests(TestCase):
    def test_a_runtime_error_becomes_an_import_error(self):
        # `load_pyrepl_hacks` imports one module and nothing else, so breaking
        # every import for the length of the call breaks only that one.
        def explode(*args, **kwargs):
            raise RuntimeError("no terminal here")

        with (
            mock.patch("builtins.__import__", explode),
            self.assertRaises(ImportError) as context,
        ):
            repl.load_pyrepl_hacks()
        self.assertIn("no terminal here", str(context.exception))


class CanUsePyreplTests(TestCase):
    def test_reports_what_pyrepl_reports(self):
        usable, reason = repl.can_use_pyrepl()
        self.assertIsInstance(usable, bool)
        self.assertIsInstance(reason, str)

    def test_a_missing_module_is_not_usable(self):
        with mock.patch.dict("sys.modules", {"_pyrepl.main": None}):
            usable, reason = repl.can_use_pyrepl()
        self.assertFalse(usable)
        self.assertTrue(reason)
