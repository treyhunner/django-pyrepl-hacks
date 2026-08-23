"""Tests for resolving and applying key bindings."""

from unittest import TestCase, mock

from django.core.exceptions import ImproperlyConfigured

from django_pyrepl_hacks import bindings
from django_pyrepl_hacks.bindings import (
    DEFAULT_BINDINGS,
    Insert,
    apply_bindings,
    describe,
    insert,
    resolve_bindings,
)


class ResolveBindingsTests(TestCase):
    def test_defaults_are_used_when_nothing_is_configured(self):
        self.assertEqual(resolve_bindings(), DEFAULT_BINDINGS)

    def test_defaults_are_not_mutated(self):
        resolve_bindings({"Alt+M": "home", "F4": "dedent"})
        self.assertEqual(DEFAULT_BINDINGS["Alt+M"], "move-to-indentation")
        self.assertNotIn("F4", DEFAULT_BINDINGS)

    def test_overrides_replace_and_extend_defaults(self):
        bindings = resolve_bindings({"Alt+M": "home", "F4": "dedent"})
        self.assertEqual(bindings["Alt+M"], "home")
        self.assertEqual(bindings["F4"], "dedent")
        self.assertEqual(bindings["End"], "end")

    def test_none_removes_a_single_default(self):
        bindings = resolve_bindings({"Home": None})
        self.assertNotIn("Home", bindings)
        self.assertIn("End", bindings)

    def test_defaults_can_be_turned_off_entirely(self):
        bindings = resolve_bindings({"F4": "dedent"}, use_defaults=False)
        self.assertEqual(bindings, {"F4": "dedent"})


class InsertTests(TestCase):
    def test_insert_returns_an_insert_binding(self):
        self.assertEqual(insert("hello"), Insert("hello"))

    def test_insert_bindings_compare_equal(self):
        self.assertEqual(insert("x"), insert("x"))
        self.assertNotEqual(insert("x"), insert("y"))


class ApplyBindingsTests(TestCase):
    def setUp(self):
        self.repl = mock.Mock()
        patcher = mock.patch.dict("sys.modules", {"pyrepl_hacks": self.repl})
        patcher.start()
        self.addCleanup(patcher.stop)
        # Asking the reader what commands exist needs a terminal.
        known = mock.patch.object(
            bindings,
            "_known_commands",
            return_value={"home", "move-to-indentation", "dedent", "kill-line"},
        )
        known.start()
        self.addCleanup(known.stop)

    def test_an_unknown_command_name_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            apply_bindings({"Ctrl+G": "hom"})
        message = str(context.exception)
        self.assertIn("PYREPL_BINDINGS['Ctrl+G']", message)
        self.assertIn("not a command", message)
        self.assertIn("'home'", message)  # suggests the near miss
        self.repl.bind.assert_not_called()

    def test_an_unknown_command_with_no_near_miss_still_reports(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            apply_bindings({"Ctrl+G": "zzzzzzzz"})
        self.assertIn("not a command", str(context.exception))

    def test_an_unusable_key_names_the_setting(self):
        self.repl.bind.side_effect = ValueError("Key combo ctrl+shift+k not supported")
        with self.assertRaises(ImproperlyConfigured) as context:
            apply_bindings({"Ctrl+Shift+K": "home"})
        message = str(context.exception)
        self.assertIn("PYREPL_BINDINGS['Ctrl+Shift+K']", message)
        self.assertIn("not a usable key", message)

    def test_command_names_bind_directly(self):
        apply_bindings({"Alt+M": "move-to-indentation"})
        self.repl.bind.assert_called_once_with("Alt+M", "move-to-indentation")

    def test_insert_bindings_insert_text(self):
        apply_bindings({"Ctrl+N": insert("[1, 2, 3]")})
        self.repl.bind_to_insert.assert_called_once_with("Ctrl+N", "[1, 2, 3]")

    def test_functions_are_registered_and_bound(self):
        def show_time(reader):
            """A command that takes just a reader."""

        apply_bindings({"F4": show_time})
        self.repl.register_command.assert_called_once_with(
            "show-time",
            with_event=False,
        )
        self.repl.register_command.return_value.assert_called_once_with(show_time)
        self.repl.bind.assert_called_once_with("F4", "show-time")

    def test_functions_taking_an_event_are_registered_with_it(self):
        def show_time(reader, event_name, event):
            """A command that takes the event too."""

        apply_bindings({"F4": show_time})
        self.repl.register_command.assert_called_once_with("show-time", with_event=True)

    def test_a_callable_with_no_readable_signature_is_still_bound(self):
        # `inspect.signature(dict)` raises ValueError, since C never described
        # it. That is not a reason to refuse the binding.
        apply_bindings({"F4": dict})
        self.repl.register_command.assert_called_once_with("dict", with_event=False)
        self.repl.bind.assert_called_once_with("F4", "dict")

    def test_lambdas_are_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            apply_bindings({"F4": lambda reader: None})
        self.assertIn("lambda", str(context.exception))

    def test_other_values_are_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            apply_bindings({"F4": 42})
        self.assertIn("PYREPL_BINDINGS['F4']", str(context.exception))


class KnownCommandsTests(TestCase):
    """The real `_known_commands`, which the tests above deliberately mock.

    Whether a reader can be built depends on whether the suite is run from a
    terminal, so these force the answer rather than reading the environment.
    An earlier version asserted the sandbox's answer and passed in CI while
    failing on a developer's machine, which is the wrong way round.
    """

    def setUp(self):
        self.repl = mock.Mock()
        patcher = mock.patch.dict("sys.modules", {"pyrepl_hacks": self.repl})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_no_reader_means_no_validation_rather_than_an_error(self):
        """A downstream test standing in for pyrepl_hacks must still work.

        Building a reader opens the tty, which a test runner has not got.
        Raising made `manage.py shell` unmockable from the outside and broke
        a downstream suite that stubbed `pyrepl_hacks` (0.1.1).
        """
        with mock.patch.dict(
            "sys.modules",
            {"_pyrepl.simple_interact": None},  # importing None raises
        ):
            self.assertIsNone(bindings._known_commands())

    def test_binding_still_works_with_no_reader_to_validate_against(self):
        with mock.patch.object(bindings, "_known_commands", return_value=None):
            apply_bindings({"Alt+M": "move-to-indentation"})
        self.repl.bind.assert_called_once_with("Alt+M", "move-to-indentation")

    def test_a_reader_that_answers_is_used_to_validate(self):
        reader = mock.Mock(commands={"home", "dedent"})
        with mock.patch.dict(
            "sys.modules",
            {"_pyrepl.simple_interact": mock.Mock(_get_reader=lambda: reader)},
        ):
            self.assertEqual(bindings._known_commands(), {"home", "dedent"})


class DescribeTests(TestCase):
    def test_command_names_describe_themselves(self):
        self.assertEqual(describe("Alt+M", "dedent"), "dedent")

    def test_inserts_show_their_text(self):
        self.assertEqual(describe("Ctrl+N", insert("hi")), "insert 'hi'")

    def test_functions_show_their_command_name(self):
        def show_time(reader):
            """A command."""

        self.assertEqual(describe("F4", show_time), "show-time")

    def test_a_target_of_the_wrong_shape_is_rejected(self):
        # Nothing has validated the setting by this point: `--show-bindings`
        # reads it and describes it, and that is the whole path.
        with self.assertRaises(ImproperlyConfigured) as context:
            describe("F4", 42)
        message = str(context.exception)
        self.assertIn("PYREPL_BINDINGS['F4']", message)
        self.assertIn("42", message)
