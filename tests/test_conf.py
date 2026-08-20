"""Tests for reading the PYREPL_* settings."""

from unittest import TestCase

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_pyrepl_hacks import conf
from django_pyrepl_hacks.bindings import DEFAULT_BINDINGS


def a_hook():
    """A setup hook that PYREPL_SETUP tests import by path."""
    a_hook.calls += 1


a_hook.calls = 0


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


class GetSetupHooksTests(TestCase):
    def test_empty_without_settings(self):
        self.assertEqual(conf.get_setup_hooks(), [])

    @override_settings(PYREPL_SETUP="tests.test_conf.a_hook")
    def test_a_single_import_path_works(self):
        self.assertEqual(conf.get_setup_hooks(), [a_hook])

    @override_settings(PYREPL_SETUP=a_hook)
    def test_a_single_callable_works(self):
        self.assertEqual(conf.get_setup_hooks(), [a_hook])

    @override_settings(PYREPL_SETUP=["tests.test_conf.a_hook", a_hook])
    def test_a_list_works(self):
        self.assertEqual(conf.get_setup_hooks(), [a_hook, a_hook])

    @override_settings(PYREPL_SETUP="tests.test_conf.no_such_hook")
    def test_an_unimportable_path_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            conf.get_setup_hooks()

    @override_settings(PYREPL_SETUP=[42])
    def test_a_non_callable_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            conf.get_setup_hooks()

    @override_settings(PYREPL_SETUP=None)
    def test_none_means_no_hooks(self):
        self.assertEqual(conf.get_setup_hooks(), [])

    @override_settings(PYREPL_SETUP=42)
    def test_something_that_is_neither_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            conf.get_setup_hooks()
