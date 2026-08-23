# django-pyrepl-hacks 🐍

[![PyPI][pypi-badge]][pypi]
[![CI][ci-badge]][ci]
[![Coverage][coverage-badge]][coverage]

A Django `shell` that uses the new Python REPL, with [pyrepl-hacks][] key bindings.

This package teaches `manage.py shell` about the new Python REPL (3.13+), adds some additional key bindings to the new REPL, and adds utilities for customizing the REPL.


## Supported Python versions 📌

This builds on [pyrepl-hacks][], which uses Python's internal `_pyrepl` module.
That module is private, so this package supports only the Python versions it has been tested against, and `requires-python` says which those are.
A newer Python will refuse to install it until a release here widens that.

If the new REPL cannot run, the `pyrepl` interface steps aside and Django moves on to IPython, bpython, or `code.interact`, exactly as it would if this package were not installed.


## Installing 💾

This needs Python 3.13, 3.14, or 3.15 and Django 5.2 or later.

Install with uv:

```console
uv add django-pyrepl-hacks
```

Or with pip:

```console
python -m pip install django-pyrepl-hacks
```

Then add it to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    "django_pyrepl_hacks",
    # ...
]
```

Now `manage.py shell` will use the new REPL:

```console
$ ./manage.py shell
14 objects imported automatically (use -v 2 for details).

>>>
```


## Default key bindings ⌨️

| Key         | Command               | What it does                                |
| ----------- | --------------------- | ------------------------------------------- |
| `Home`      | `home`                | Move to the first character in the input    |
| `End`       | `end`                 | Move to the last character in the input     |
| `Alt+M`     | `move-to-indentation` | Move to the first non-space in the line     |
| `Shift+Tab` | `dedent`              | Dedent the whole input                      |
| `Alt+Down`  | `move-line-down`      | Swap the current line with the next one     |
| `Alt+Up`    | `move-line-up`        | Swap the current line with the previous one |
| `Ctrl+Up`   | `previous-history`    | Move to the previous history entry          |
| `Ctrl+Down` | `next-history`        | Move to the next history entry              |
| `Alt+{`     | `previous-paragraph`  | Move to the previous blank line             |
| `Alt+}`     | `next-paragraph`      | Move to the next blank line                 |

To see what is actually bound in your project, including your own additions:

```console
./manage.py shell --show-bindings
```


## Settings ⚙️

Every setting is optional.


### `PYREPL_BINDINGS`

A dictionary mapping a key to the thing that key should do, layered over the defaults above.

The keys should be human-readable key bindings: `"Ctrl+K"`, `"Alt+Up"`, `"Shift+Tab"`, `"F4"`, `"Home"`, `"PageUp"`, or a sequence like `"Ctrl+X Ctrl+R"`.

The values must be either:

1. A string representing the name of an installed `_pyrepl` command
2. A function, representing a new `_pyrepl` command
3. `django_pyrepl_hacks.insert("some text")` to insert text

#### Using an existing `_pyrepl` command

There are about 50 built-in key commands to `_pyrepl`: `show-history`, `paste-mode`, `transpose-characters`, `yank`, `yank-pop`, `unix-word-rubout`, `backward-word`, `forward-word`, and `history-search-backward` are some of the more useful ones.

[pyrepl-hacks][] adds `dedent`, `move-line-up`, `move-line-down`, `move-to-indentation`, `previous-paragraph`, and `next-paragraph`.

These are the default key bindings (you don't need to set these):

```python
PYREPL_BINDINGS = {
    "Home": "home",
    "End": "end",
    "Alt+M": "move-to-indentation",
    "Shift+Tab": "dedent",
    "Alt+Down": "move-line-down",
    "Alt+Up": "move-line-up",
    "Ctrl+Up": "previous-history",
    "Ctrl+Down": "next-history",
    "Alt+{": "previous-paragraph",
    "Alt+}": "next-paragraph",
}
```

Note that by default, the `home` and `end` keys will move to the first character and the last character in the current code block, which is different from their default behavior in the REPL.

#### Defining a new command

Setting a `PYREPL_BINDINGS` value to a function object will register that function as a `_pyrepl` new command.
The new command will be named after the function, with underscores replaced by hyphens, so the `sql_of_last_query` function below will register as a command named `sql-of-last-query`.

Functions are called with the pyrepl's `reader` object, which holds the text you are editing:

```python
# myproject/repl_extensions.py
def sql_of_last_query(reader):
    """Type out the SQL of the most recent query."""
    from django.db import connection

    if connection.queries:
        reader.insert(connection.queries[-1]["sql"])
```

```python
from myproject.repl_extensions import sql_of_last_query

PYREPL_BINDINGS = {"F9": sql_of_last_query}
```

A function taking three arguments is called with the event too (just as [pyrepl-hacks][] commands with `with_event=True` are).
This is needed to move the cursor, since movement commands require the event object:

```python
import pyrepl_hacks as repl


def filter_call(reader, event_name, event):
    """Type `User.objects.filter()` and park the cursor inside the parens."""
    reader.insert("User.objects.filter()")
    repl.commands.left(reader, event_name, event)
```

Lambda functions are not allowed.


#### Inserting text

Here are two example bindings that insert text:

```python
from django_pyrepl_hacks import insert

PYREPL_BINDINGS = {
    "Ctrl+F": insert("User.objects.filter("),
    "F9": insert("connection.queries[-1]['sql']"),
}
```

Hitting `Ctrl+F` will insert `User.objects.filter(` and hitting `F9` will insert `connection.queries[-1]['sql']`.


### Disabling a key binding

Using `None` as the value to a `PYREPL_BINDINGS` item will reset that binding back to its `_pyrepl` default.

If you would prefer the `Home` and `End` keys had their default behaviors (moving to the beginning/end of a line instead of the whole block) you could do this:

```python
PYREPL_BINDINGS = {
    "Home": None,
    "End": None,
}
```


### `PYREPL_USE_DEFAULT_BINDINGS`

Set to `False` to turn off the default key bindings listed above.
The [pyrepl-hacks][] commands they point at are still registered, so you can bind your own keys to them.


### `PYREPL_THEME`

Use this to customize the syntax highlighting colors for the code you type at the REPL.

The keys are the eleven token types that `_pyrepl` knows about, and the values are colors:

```python
PYREPL_THEME = {
    "string": "green",
    "number": "intense blue",
    "comment": "grey",
    "keyword": "bold magenta",
    "prompt": "bold green",
}
```

The token types:

| Token              | What it colors                          |
| ------------------ | --------------------------------------- |
| `prompt`           | The `>>>` and `...` prompts             |
| `keyword`          | `def`, `if`, `for`, `import`, `return`  |
| `keyword_constant` | `None`, `True`, `False`                 |
| `soft_keyword`     | `match`, `case`, `type`                 |
| `builtin`          | `len`, `print`, `sorted`                |
| `comment`          | `# like this`                           |
| `string`           | `"like this"`                           |
| `number`           | `42`, `3.14`                            |
| `op`               | `+`, `-`, `=`, `(`, `,`                 |
| `definition`       | The name in `def name` or `class Name`  |
| `reset`            | Everything else, and the default style  |

The colors are:

| Color     | `bold` | `intense` | `background` | `intense background` |
| --------- | ------ | --------- | ------------ | -------------------- |
| `black`   | yes    | yes       | yes          | yes                  |
| `blue`    | yes    | yes       | yes          | yes                  |
| `cyan`    | yes    | yes       | yes          | yes                  |
| `green`   | yes    | yes       | yes          | yes                  |
| `grey`    | no     | no        | no           | no                   |
| `magenta` | yes    | yes       | yes          | yes                  |
| `red`     | yes    | yes       | yes          | yes                  |
| `white`   | yes    | yes       | yes          | yes                  |
| `yellow`  | yes    | yes       | yes          | yes                  |

Every color works on its own.
`grey` is the exception to the prefixes below: there is no `bold grey`, and asking for one is an error.

The prefixes are:

| Specification              | Example                          |
| -------------------------- | -------------------------------- |
| plain                      | `"red"`                          |
| `bold`                     | `"bold red"`                     |
| `intense`                  | `"intense red"`                  |
| `background`               | `"background red"`               |
| `intense background`       | `"intense background red"`       |
| combined with a comma      | `"background black, bold white"` |
| nothing at all             | `"reset"`                        |

Here's a theme that works well with the Solarized Light theme I use in my Terminal:

```python
PYREPL_THEME = {
    "keyword": "green",
    "builtin": "blue",
    "comment": "intense blue",
    "string": "cyan",
    "number": "cyan",
    "definition": "blue",
    "soft_keyword": "bold green",
    "op": "intense green",
    "reset": "reset, intense green",
}
```

Any value you leave out keeps the REPL's default color.

Named themes (`PYREPL_THEME = "solarized-light"`) are not (yet) implemented.

This setting needs Python 3.14 or later.
On an older Python it is ignored and the REPL keeps its own colors, so a project running on both versions can set it once without breaking the shell for anyone.
`manage.py check` warns that it is doing nothing there.


### `PYREPL_SETUP`

This is an escape hatch: a place to put code that should run when the REPL starts and nowhere else.

This is the import path of a function, called once the REPL is configured and just before it starts:

```python
PYREPL_SETUP = "myproject.repl.setup"
```

An import path rather than the function itself, because `settings.py` is read by every process you run and this is code only the REPL needs.
To do more than one thing, call them from that one function.

Below are some example uses for that function that `PYREPL_SETUP` points to.

#### Indicating the environment in your prompt

Here the management shell prompt would become `prod>>>` and `prod...` when `settings.DEBUG` isn't `True`:

```python
def setup():
    import sys
    from django.conf import settings

    if not settings.DEBUG:
        sys.ps1, sys.ps2 = "prod>>> ", "prod... "
```

#### A custom banner

To print something each time the REPL launches:

```python
def setup():
    import django
    from django.db import connections

    database = connections["default"].settings_dict["NAME"]
    print(f"Django {django.get_version()} | {database}")
```


## Checks ✅

`manage.py check` validates the `PYREPL_*` settings it can, so a mistake turns up before you are staring at a broken prompt.

Everything it reports is a warning rather than an error.

There are four mistakes it cannot catch:

1. a command name that does not exist
2. a key combination that cannot be spelled
3. a `PYREPL_SETUP` path that does not import, or does not point at a callable
4. a color name that does not exist

The first two need a REPL reader, and building one needs a terminal that `manage.py check` may not have.
The third would mean importing your hook into every `migrate`, which is what naming it as a path exists to avoid.

All four are caught when the shell starts, and reported against the setting they came from:

```console
$ ./manage.py shell
CommandError: Could not set up the REPL: PYREPL_BINDINGS['Ctrl+G'] is 'hom', which is not a command. Did you mean 'home'?
```

`manage.py shell --show-bindings` is the easiest way to check your configuration, since it resolves the same settings without starting a REPL.


## Contributing 🤝

See [CONTRIBUTING.md][].


[pyrepl-hacks]: https://github.com/treyhunner/pyrepl-hacks
[CONTRIBUTING.md]: CONTRIBUTING.md
[pypi-badge]: https://img.shields.io/pypi/v/django-pyrepl-hacks.svg
[pypi]: https://pypi.org/project/django-pyrepl-hacks/
[ci-badge]: https://github.com/treyhunner/django-pyrepl-hacks/actions/workflows/ci.yml/badge.svg
[ci]: https://github.com/treyhunner/django-pyrepl-hacks/actions/workflows/ci.yml
[coverage-badge]: https://codecov.io/gh/treyhunner/django-pyrepl-hacks/branch/main/graph/badge.svg
[coverage]: https://codecov.io/gh/treyhunner/django-pyrepl-hacks
