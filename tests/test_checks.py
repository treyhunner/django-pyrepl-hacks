"""Tests for the PYREPL_* system checks."""

from unittest import TestCase, mock

from django.test import override_settings

from django_pyrepl_hacks import repl
from django_pyrepl_hacks.checks import check_settings


def ids(errors):
    return [error.id for error in errors]


class CheckSettingsTests(TestCase):
    def test_no_complaints_by_default(self):
        self.assertEqual(check_settings(), [])

    @override_settings(PYREPL_BINDINGS=["F4"])
    def test_a_non_dictionary_binding_setting_is_caught(self):
        self.assertEqual(ids(check_settings()), ["pyrepl_hacks.E001"])

    @override_settings(PYREPL_BINDINGS={"F4": 42})
    def test_a_nonsense_binding_target_is_caught(self):
        self.assertEqual(ids(check_settings()), ["pyrepl_hacks.E002"])

    @override_settings(PYREPL_BINDINGS={"F4": lambda reader: None})
    def test_a_lambda_binding_is_caught(self):
        [error] = check_settings()
        self.assertEqual(error.id, "pyrepl_hacks.E003")

    @override_settings(PYREPL_THEME="red")
    def test_a_non_dictionary_theme_is_caught(self):
        self.assertEqual(ids(check_settings()), ["pyrepl_hacks.E004"])

    @override_settings(PYREPL_THEME={"string": "red"})
    def test_a_theme_on_too_old_a_python_is_caught(self):
        with mock.patch.object(repl, "THEME_REQUIRES", (99, 0)):
            [warning] = check_settings()
        self.assertEqual(warning.id, "pyrepl_hacks.W001")

    @override_settings(PYREPL_THEME={"strng": "red"})
    def test_a_misspelled_theme_token_is_caught(self):
        with mock.patch.object(repl, "THEME_REQUIRES", (3, 13)):
            [error] = check_settings()
        self.assertEqual(error.id, "pyrepl_hacks.E005")
        self.assertIn("strng", error.msg)
        self.assertIn("string", error.hint)

    @override_settings(PYREPL_THEME={"string": "red", "number": "blue"})
    def test_known_theme_tokens_pass(self):
        with mock.patch.object(repl, "THEME_REQUIRES", (3, 13)):
            self.assertEqual(check_settings(), [])

    @override_settings(PYREPL_SETUP="tests.test_checks.no_such_hook")
    def test_an_unimportable_setup_hook_is_caught(self):
        self.assertEqual(ids(check_settings()), ["pyrepl_hacks.E006"])
