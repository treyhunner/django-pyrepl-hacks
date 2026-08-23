"""Tests for the PYREPL_* system checks."""

from unittest import TestCase, mock

from django.core.checks import ERROR, WARNING
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
        self.assertEqual(ids(check_settings()), ["pyrepl_hacks.W002"])

    @override_settings(PYREPL_BINDINGS={"F4": 42})
    def test_a_nonsense_binding_target_is_caught(self):
        self.assertEqual(ids(check_settings()), ["pyrepl_hacks.W003"])

    @override_settings(PYREPL_BINDINGS={"F4": lambda reader: None})
    def test_a_lambda_binding_is_caught(self):
        [error] = check_settings()
        self.assertEqual(error.id, "pyrepl_hacks.W004")

    @override_settings(PYREPL_THEME="red")
    def test_a_non_dictionary_theme_is_caught(self):
        self.assertEqual(ids(check_settings()), ["pyrepl_hacks.W005"])

    @override_settings(PYREPL_THEME={"string": "red"})
    def test_a_theme_on_too_old_a_python_is_caught(self):
        with mock.patch.object(repl, "THEME_REQUIRES", (99, 0)):
            [warning] = check_settings()
        self.assertEqual(warning.id, "pyrepl_hacks.W001")
        self.assertIn("no effect", warning.msg)

    @override_settings(PYREPL_THEME={"strng": "red"})
    def test_a_misspelled_theme_token_is_caught(self):
        with mock.patch.object(repl, "THEME_REQUIRES", (3, 13)):
            [error] = check_settings()
        self.assertEqual(error.id, "pyrepl_hacks.W006")
        self.assertIn("strng", error.msg)
        self.assertIn("string", error.hint)

    @override_settings(PYREPL_THEME={"string": "red", "number": "blue"})
    def test_known_theme_tokens_pass(self):
        with mock.patch.object(repl, "THEME_REQUIRES", (3, 13)):
            self.assertEqual(check_settings(), [])

    @override_settings(PYREPL_SETUP=42)
    def test_a_nonsense_setup_setting_is_caught(self):
        self.assertEqual(ids(check_settings()), ["pyrepl_hacks.W007"])

    @override_settings(PYREPL_SETUP="tests.test_checks.no_such_hook")
    def test_an_unimportable_setup_hook_is_left_alone(self):
        """Resolving it would import REPL-only code during every migrate."""
        self.assertEqual(check_settings(), [])

    def test_nothing_here_ever_blocks_another_command(self):
        """An Error would abort migrate and collectstatic over a key binding.

        `shell` sets requires_system_checks = [], so these never run for the
        command they describe; they only ever reach other commands.
        """
        settings_that_are_wrong = [
            {"PYREPL_BINDINGS": ["F4"]},
            {"PYREPL_BINDINGS": {"F4": 42}},
            {"PYREPL_BINDINGS": {"F4": lambda reader: None}},
            {"PYREPL_THEME": "red"},
            {"PYREPL_THEME": {"strng": "red"}},
            {"PYREPL_SETUP": 42},
        ]
        for wrong in settings_that_are_wrong:
            with self.subTest(**wrong), override_settings(**wrong):
                with mock.patch.object(repl, "THEME_REQUIRES", (3, 13)):
                    found = check_settings()
                self.assertTrue(found, "expected this to be reported")
                for problem in found:
                    self.assertTrue(problem.is_serious(WARNING), problem)
                    self.assertFalse(problem.is_serious(ERROR), problem)
