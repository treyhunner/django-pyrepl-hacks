`django-pyrepl-hacks` gives Django's `shell` command a `pyrepl` interface: the REPL that ships with Python 3.13 and later, with Django's auto-imported namespace and [pyrepl-hacks][] key bindings.
See `README.md` for the settings, and `CONTRIBUTING.md` for the development workflow.

It started as a `common/management/commands/shell.py` copied between two of Trey's Django projects.
Everything beyond that file is configuration, so that the copy does not have to be edited in each project.

## Commands

This project uses uv and just.
Run `just` to see every available task; `just setup` installs the git hooks.
Run `just check` (format, lint, type check, and test) before finishing a change.

Tests run on Python 3.13 and 3.14 and are checked against Django 5.2, 6.0, and 6.1 in CI.
There is no Django project in the repository: `runtests.py` points at `tests/settings.py` and runs Django's own test runner.

## Things the code cannot tell you

- **Importing `pyrepl_hacks` needs a terminal.**
  It registers commands at import time, and registering a command builds a REPL reader, which opens the tty.
  So no module here may import it at module level.
  `bindings.py` and `repl.py` import it inside functions, and `checks.py` and `conf.py` never import it at all, because a system check has to run in CI.
  This is also why `insert()` lives in `bindings.py` and returns a plain dataclass: settings modules import it, and reading settings must not touch `_pyrepl`.

- **An `ImportError` out of a shell interface means "not available here".**
  Django's `handle` catches it and moves to the next entry in `shells`.
  That is exactly the right signal for "no tty", and exactly the wrong one for "your `PYREPL_THEME` is broken", which is why `pyrepl()` gates on `can_use_pyrepl()` and `load_pyrepl_hacks()` first and converts every later `ImportError` into a `CommandError`.
  Without that, a typo in a setting silently downgraded the user to `code.interact` with no explanation.
  There is a test for it.

- **`interactive_console` falls back to `sys._baserepl()` when it cannot run, and that drops the namespace.**
  All the work of auto-importing models would be thrown away.
  So `can_use_pyrepl()` asks `_pyrepl.main.CAN_USE_PYREPL` beforehand and declines the interface rather than letting the fallback happen.

- **`PYREPL_THEME` needs Python 3.14.**
  `_colorize.Syntax`, which `pyrepl_hacks.update_theme` builds a theme out of, does not exist in 3.13.
  `repl.THEME_REQUIRES` is the one place that version lives; `checks.py` reads it through the module so a test can patch it.

- **`interactive_console` only sets `sys.ps1` and `sys.ps2` if they are missing**, which is why a `PYREPL_SETUP` hook can set the prompts: it runs first and the REPL leaves them alone.
  There were `PYREPL_PS1`, `PYREPL_PS2`, and `PYREPL_BANNER` settings for this and for a banner line.
  They were cut because a hook does both in four lines, and the banner alone was a quarter of the package.
  `PYREPL_SETUP` is the only primitive here; everything else is a declarative convenience over it, and each one has to earn that.

- **A system check must never be an `Error` here.**
  `shell` sets `requires_system_checks = []`, so these checks never run for the command they describe; the commands that do run them are `migrate` and `collectstatic`.
  An `Error` therefore cannot help the person with the broken setting and can only block a deploy over a key binding.
  For the same reason `checks.py` validates the *shape* of `PYREPL_SETUP` without importing it: resolving the path would drag REPL-only code into every migrate.

- **Two mistakes can only be caught with a live reader**, so they live in `apply_bindings` rather than in `checks.py`: a command name the reader does not know, and a key combination `to_keyspec` cannot spell.
  `Reader.bind` appends to the keymap without validating and resolves at keypress time, so an unchecked typo binds cleanly and leaves the key silently dead.
  `_known_commands()` returns `None` rather than raising when no reader can be built, because a downstream project's tests stand in for `pyrepl_hacks` and have no tty: raising made this package unmockable from the outside and broke Python Morsels' shell tests in 0.1.1.

## Deliberately not done yet

- **Named themes.**
  `PYREPL_THEME` takes a dictionary today, and it should eventually also take a name: `PYREPL_THEME = "solarized-light"`.
  Trey's [solarized-light-repl][] is the shape of the answer, and the palettes could come from there or live here.
  A string is currently unreachable as a theme value, so adding this later is additive rather than breaking.

## Testing notes

The REPL itself cannot be exercised by the test suite, since it needs a tty.
Tests mock `repl.can_use_pyrepl`, `repl.load_pyrepl_hacks`, `repl.setup`, and `_pyrepl.main.interactive_console`, and `sys.modules["pyrepl_hacks"]` is mocked where the calls into it are what is being checked.

That leaves a real gap: nothing here proves a key binding actually fires.
Verify that by hand under a pty, or by pointing a real project at a checkout, when changing anything in `bindings.py`.

[pyrepl-hacks]: https://github.com/treyhunner/pyrepl-hacks
[solarized-light-repl]: https://pypi.org/project/solarized-light-repl/
