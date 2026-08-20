"""Tests for resolving and applying key bindings."""

from unittest import TestCase, mock

from django.core.exceptions import ImproperlyConfigured

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

    def test_lambdas_are_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            apply_bindings({"F4": lambda reader: None})
        self.assertIn("lambda", str(context.exception))

    def test_other_values_are_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as context:
            apply_bindings({"F4": 42})
        self.assertIn("PYREPL_BINDINGS['F4']", str(context.exception))


class DescribeTests(TestCase):
    def test_command_names_describe_themselves(self):
        self.assertEqual(describe("dedent"), "dedent")

    def test_inserts_show_their_text(self):
        self.assertEqual(describe(insert("hi")), "insert 'hi'")

    def test_functions_show_their_command_name(self):
        def show_time(reader):
            """A command."""

        self.assertEqual(describe(show_time), "show-time")
