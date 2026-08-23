# Changelog


## 0.2.0 (2026-08-23)

Python 3.15 support, one breaking change, and two settings that made more noise about a problem than the problem was worth.

- Python 3.15 is supported.
  This needs [pyrepl-hacks][] 0.6 or later, which is now the minimum
- Breaking: `PYREPL_SETUP` takes a single import path.
  A callable, or a list of either, is now rejected by the system check and again when the REPL starts.
  A callable has to be imported by `settings.py`, which every process reads, and this is REPL-only code.
  A list said what one hook calling two functions already says, in Python, where the order is there to read.
  The two together were also ambiguous: a string is a sequence, so `PYREPL_SETUP = [*PYREPL_SETUP, hook]` in a local settings file split the base path into single characters, and `manage.py check` reported no issues
- `PYREPL_THEME` is ignored on Python 3.13 instead of refusing to start the shell.
  Setting it there is a Python that cannot honor it, not a mistake in it, and refusing left a teammate on 3.13 with no shell at all because someone on 3.14 wanted colors.
  `manage.py check` still warns that the setting is doing nothing there
- `manage.py shell --show-bindings` reports a binding target it cannot describe, instead of printing its repr.
  Printing it passed the only pre-flight there is, and then the shell failed at startup on the same setting


## 0.1.2 (2026-08-21)

- Fix a regression in 0.1.1 that made the shell command impossible to mock.
  Validating a command name needs a REPL reader, and asking for one raised
  under a test runner, so a project testing its own shell wiring by standing
  in for `pyrepl-hacks` got a `RuntimeError`. With no reader there is nothing
  real to validate against, so validation is now skipped rather than raised

## 0.1.1 (2026-08-21)

Fixes for how configuration mistakes are reported. No API changes.

- System checks are warnings rather than errors.
  As errors they aborted `migrate` and `collectstatic` over a REPL setting,
  while never running for `shell` itself, which sets
  `requires_system_checks = []`
- The `PYREPL_SETUP` check no longer imports the hook, which pulled REPL-only
  code into every `migrate`
- A command name that does not exist is now rejected when the shell starts,
  with a suggestion. It used to bind cleanly and leave the key doing nothing
- A key combination that cannot be spelled now names the setting it came from,
  instead of escaping as a raw `ValueError` traceback
- `manage.py shell --show-bindings` reports a bad setting instead of raising
  the exception it exists to warn about
- Removed a redundant `load_pyrepl_hacks()` call that sat outside the shell
  command's error handling, where an `ImportError` from it read as "interface
  unavailable" and silently downgraded the shell

## 0.1.0 (2026-08-21)

Initial release.

- A `shell` management command that prefers the new Python REPL, with Django's auto-imported models and [pyrepl-hacks][] key bindings
- `PYREPL_BINDINGS` and `PYREPL_USE_DEFAULT_BINDINGS` for key bindings
- `PYREPL_THEME` for syntax highlighting colors (Python 3.14 and later)
- `PYREPL_SETUP` for anything else, including custom prompts and banners
- `manage.py shell --show-bindings` to see what is bound
- System checks for every setting

[pyrepl-hacks]: https://github.com/treyhunner/pyrepl-hacks
