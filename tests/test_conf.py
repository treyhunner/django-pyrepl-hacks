"""Tests for reading the PYREPL_* settings."""

from unittest import TestCase

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_pyrepl_hacks import conf
from django_pyrepl_hacks.bindings import DEFAULT_BINDINGS


def a_hook():
    """A setup hook that PYREPL_SETUP tests import by path."""


#: Something importable that PYREPL_SETUP cannot use, for the same reason
#: `PYREPL_SETUP = "myproject.settings.DEBUG"` would not work.
not_a_hook = 42


class GetBindingsTests(TestCase):
    def test_defaults_without_settings(self):
        self.assertEqual(conf.get_bindings(), DEFAULT_BINDINGS)

    @override_settings(PYREPL_BINDINGS={"F4": "dedent"})
    def test_settings_are_merged_in(self):
        self.assertEqual(conf.get_bindings()["F4"], "dedent")

    @override_settings(PYREPL_USE_DEFAULT_BINDINGS=False)
    def test_defaults_can_be_turned_off(self):
        self.assertEqual(conf.get_bindings(), {})

    @override_settings(PYREPL_BINDINGS=["F4", "dedent"])
    def test_non_dictionary_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            conf.get_bindings()


class GetThemeTests(TestCase):
    def test_empty_without_settings(self):
        self.assertEqual(conf.get_theme(), {})

    @override_settings(PYREPL_THEME={"string": "red"})
    def test_theme_is_returned(self):
        self.assertEqual(conf.get_theme(), {"string": "red"})

    @override_settings(PYREPL_THEME="red")
    def test_non_dictionary_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            conf.get_theme()


class GetSetupHookTests(TestCase):
    def test_none_without_settings(self):
        self.assertIsNone(conf.get_setup_hook())

    @override_settings(PYREPL_SETUP="tests.test_conf.a_hook")
    def test_an_import_path_is_resolved(self):
        self.assertEqual(conf.get_setup_hook(), a_hook)

    @override_settings(PYREPL_SETUP=None)
    def test_none_means_no_hook(self):
        self.assertIsNone(conf.get_setup_hook())

    @override_settings(PYREPL_SETUP="tests.test_conf.no_such_hook")
    def test_an_unimportable_path_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            conf.get_setup_hook()
        self.assertIn("could not import", str(context.exception))

    @override_settings(PYREPL_SETUP="tests.test_conf.not_a_hook")
    def test_a_path_to_something_uncallable_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            conf.get_setup_hook()
        self.assertIn("not callable", str(context.exception))

    @override_settings(PYREPL_SETUP=a_hook)
    def test_a_callable_is_rejected(self):
        """settings.py is read by every process, and this is REPL-only code."""
        with self.assertRaises(ImproperlyConfigured) as context:
            conf.get_setup_hook()
        self.assertIn("import path string", str(context.exception))

    @override_settings(PYREPL_SETUP=["tests.test_conf.a_hook"])
    def test_a_list_is_rejected(self):
        """A hook that calls two functions says this in Python, in order."""
        with self.assertRaises(ImproperlyConfigured) as context:
            conf.get_setup_hook()
        self.assertIn("import path string", str(context.exception))


class ValidateSetupTests(TestCase):
    """The shape check that runs as a system check, without importing hooks."""

    def test_nothing_configured_passes(self):
        conf.validate_setup()

    @override_settings(PYREPL_SETUP="tests.test_conf.no_such_hook")
    def test_an_import_path_is_not_resolved(self):
        """Resolving it would import REPL-only code during every migrate."""
        conf.validate_setup()

    @override_settings(PYREPL_SETUP=a_hook)
    def test_a_callable_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            conf.validate_setup()
        self.assertIn("import path string", str(context.exception))
