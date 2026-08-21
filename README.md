# django-pyrepl-hacks 🐍

[![PyPI][pypi-badge]][pypi]
[![CI][ci-badge]][ci]
[![Coverage][coverage-badge]][coverage]

A Django `shell` that uses the new Python REPL, with [pyrepl-hacks][] key bindings.

Django's shell tries IPython, then bpython, then `code.interact`.
None of those is the REPL that ships with Python 3.13 and later, so `manage.py shell` gives you a worse REPL than `python` does.
This package adds a `pyrepl` interface and puts it first.

You get syntax highlighting, multi-line editing, and history search, plus Django's auto-imported models and a handful of extra key bindings.


## ⚠️ WARNING: here be dragons 🐉

This builds on [pyrepl-hacks][], which relies on the `_pyrepl` module.
As the `_` prefix implies, that module is not designed for public use, and a new Python release may break it.

So this package pins its supported Python versions to the ones known to work.


## Installing 💾

This needs Python 3.13 or 3.14 and Django 5.2 or later.

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

That's the whole setup.
`manage.py shell` will now use the new REPL:

```console
$ ./manage.py shell
14 objects imported automatically (use -v 2 for details).

>>>
```

The other interfaces are still there, so `manage.py shell -i ipython` works as before.
So does everything else the shell command does: `-c`, piped stdin, `--no-imports`, and `--no-startup`.

### A note on dependency groups

`INSTALLED_APPS` is read wherever Django starts, so this belongs with your regular dependencies rather than in a dev-only group.
A dev-only install plus an unconditional `INSTALLED_APPS` entry means production cannot start at all.

If you would rather keep it out of production, gate the entry too:

```python
if DEBUG:
    INSTALLED_APPS += ["django_pyrepl_hacks"]
```

Production then falls back to Django's own shell, which means a production shell loses the auto-imported models as well.
Shipping it is usually the smaller cost: the package is pure Python and depends on nothing but Django and [pyrepl-hacks][].


## Default key bindings ⌨️

| Key         | Command               | What it does                              |
| ----------- | --------------------- | ----------------------------------------- |
| `Home`      | `home`                | Move to the first character in the input   |
| `End`       | `end`                 | Move to the last character in the input    |
| `Alt+M`     | `move-to-indentation` | Move to the first non-space in the line    |
| `Shift+Tab` | `dedent`              | Dedent the whole input                     |
| `Alt+Down`  | `move-line-down`      | Swap the current line with the next one    |
| `Alt+Up`    | `move-line-up`        | Swap the current line with the previous one |
| `Ctrl+Up`   | `previous-history`    | Move to the previous history entry         |
| `Ctrl+Down` | `next-history`        | Move to the next history entry             |
| `Alt+{`     | `previous-paragraph`  | Move to the previous blank line            |
| `Alt+}`     | `next-paragraph`      | Move to the next blank line                |

To see what is actually bound in your project, including your own additions:

```console
./manage.py shell --show-bindings
```


## Settings ⚙️

Every setting is optional.


### `PYREPL_BINDINGS`

A dictionary mapping a key to the thing that key should do, layered over the defaults above.

The keys are human-readable: `"Ctrl+K"`, `"Alt+Up"`, `"Shift+Tab"`, `"F4"`, `"Home"`, `"PageUp"`, or a sequence like `"Ctrl+X Ctrl+R"`.

The values come in four flavors.

**1. A string is the name of a REPL command that already exists.**

```python
PYREPL_BINDINGS = {
    "Ctrl+K": "kill-line",  # Delete from the cursor to end of line
    "Alt+D": "kill-word",  # Delete the word after the cursor
    "Ctrl+L": "clear-screen",
    "Alt+<": "first-history",  # Jump to the oldest history entry
    "Alt+>": "last-history",  # Jump to the newest
    "Ctrl+O": "operate-and-get-next",  # Run this line, then offer the next one
}
```

There are about 50 of these built in.
`show-history`, `paste-mode`, `transpose-characters`, `yank`, `yank-pop`, `unix-word-rubout`, `backward-word`, `forward-word`, and `history-search-backward` are some of the more useful ones.
[pyrepl-hacks][] adds `dedent`, `move-line-up`, `move-line-down`, `move-to-indentation`, `previous-paragraph`, and `next-paragraph`.

**2. `insert(text)` types some text for you.**

```python
from django_pyrepl_hacks import insert

PYREPL_BINDINGS = {
    "Ctrl+N": insert("User.objects.filter("),
    "F5": insert("from django.test import Client\nc = Client()\n"),
    "F9": insert("connection.queries[-1]['sql']"),
}
```

**3. A function becomes a new REPL command.**

It is registered under its own name, with underscores turned into hyphens, so `sql_of_last_query` becomes the command `sql-of-last-query`.
It is called with the reader, which is the object holding the text you are editing:

```python
# myproject/repl.py
def sql_of_last_query(reader):
    """Type out the SQL of the most recent query."""
    from django.db import connection

    if connection.queries:
        reader.insert(connection.queries[-1]["sql"])
```

```python
from myproject.repl import sql_of_last_query

PYREPL_BINDINGS = {"F9": sql_of_last_query}
```

A function taking three arguments is called with the event too, the way [pyrepl-hacks][] `with_event=True` commands are.
That is what you need to move the cursor, since the movement commands take the event:

```python
import pyrepl_hacks as repl


def filter_call(reader, event_name, event):
    """Type `User.objects.filter()` and park the cursor inside the parens."""
    reader.insert("User.objects.filter()")
    repl.commands.left(reader, event_name, event)
```

Lambdas are rejected, because a command has to be registered under a name.
`manage.py check` tells you so rather than waiting until you press the key.

**4. `None` turns off one of the defaults.**

```python
PYREPL_BINDINGS = {
    "Home": None,  # Give Home back to beginning-of-line
    "Ctrl+Up": None,
}
```

Putting it together:

```python
from django_pyrepl_hacks import insert
from myproject.repl import sql_of_last_query

PYREPL_BINDINGS = {
    "Ctrl+K": "kill-line",
    "Ctrl+N": insert("User.objects.filter("),
    "F9": sql_of_last_query,
    "Home": None,
}
```

```console
$ ./manage.py shell --show-bindings
End        end
Alt+M      move-to-indentation
Shift+Tab  dedent
Alt+Down   move-line-down
Alt+Up     move-line-up
Ctrl+Up    previous-history
Ctrl+Down  next-history
Alt+{      previous-paragraph
Alt+}      next-paragraph
Ctrl+K     kill-line
Ctrl+N     insert 'User.objects.filter('
F9         sql-of-last-query
```


### `PYREPL_USE_DEFAULT_BINDINGS`

Set to `False` to start from nothing instead of from the default bindings.
`PYREPL_BINDINGS` is then the whole set.


### `PYREPL_THEME`

Syntax highlighting colors for the code you type at the prompt.
The REPL colors your input as you type it, and this changes which color each kind of token gets.

The keys are the eleven token types the REPL knows about, and the values are colors:

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

The colors are `black`, `blue`, `cyan`, `green`, `grey`, `magenta`, `red`, `white`, and `yellow`, each of which can be prefixed:

| Specification              | Example                     |
| -------------------------- | --------------------------- |
| plain                      | `"red"`                     |
| `bold`                     | `"bold red"`                |
| `intense`                  | `"intense red"`             |
| `background`               | `"background red"`          |
| `intense background`       | `"intense background red"`  |
| combined with a comma      | `"background black, bold white"` |
| nothing at all             | `"reset"`                   |

So a low-contrast theme that leaves keywords loud:

```python
PYREPL_THEME = {
    "keyword": "bold magenta",
    "keyword_constant": "bold magenta",
    "soft_keyword": "bold magenta",
    "builtin": "cyan",
    "string": "green",
    "number": "green",
    "comment": "intense black",
    "op": "reset",
    "definition": "bold blue",
}
```

Anything you leave out keeps the REPL's own color.

Named themes (`PYREPL_THEME = "solarized-light"`) are not implemented yet.
A string is not a valid value today, so they can be added without breaking a dictionary you have already written.

This setting needs Python 3.14 or later, since that is when the REPL's theme became something a program could set.
`manage.py check` warns when it is set on an older Python, and the shell refuses to start rather than pretending it worked.


### `PYREPL_SETUP`

A callable, an import path, or a list of either, called once the REPL is configured and just before it starts.

This is the escape hatch: the one place to put code that should run when the REPL starts and nowhere else.
Settings modules will not do: they are imported by every management command and by your web server too.

```python
PYREPL_SETUP = "myproject.repl.setup"
```

Here's how you'd use the full [pyrepl-hacks][] API to register a command, rather than going through `PYREPL_BINDINGS`:

```python
# myproject/repl.py
import pyrepl_hacks as repl


def setup():
    @repl.bind("Ctrl+X Ctrl+Q", with_event=True)
    def insert_query(reader, event_name, event):
        """Insert a queryset skeleton and park the cursor inside it."""
        reader.insert("User.objects.filter()")
        repl.commands.left(reader, event_name, event)
```

Import `pyrepl_hacks` inside the hook rather than at module level: importing it builds a REPL reader, which needs a terminal.

The hook is also where the settings this package deliberately does not have go.

**A prompt that tells you which environment you are in.**
The REPL only sets `sys.ps1` and `sys.ps2` if it finds them missing, so setting them in the hook means it leaves yours alone:

```python
def setup():
    import sys
    from django.conf import settings

    if not settings.DEBUG:
        sys.ps1, sys.ps2 = "prod>>> ", "prod... "
```

Worth setting up before the day you run a quick query in what turns out to be production.
A prompt is on every line, so unlike a banner it does not scroll away.

**A banner above the prompt.**

```python
def setup():
    import django
    from django.db import connections

    database = connections["default"].settings_dict["NAME"]
    print(f"Django {django.get_version()} | {database}")
```


## When the REPL cannot run 🚧

The new REPL needs a terminal, and it refuses to start under `PYTHON_BASIC_REPL` or on an old Windows.
When that happens the `pyrepl` interface steps aside and Django moves on to IPython, bpython, or `code.interact`, exactly as it would if this package were not installed.

A mistake in your own configuration is a different thing: the shell reports it rather than quietly falling back to a plain REPL.


## Checks ✅

`manage.py check` validates every `PYREPL_*` setting, so a typo turns up before you are staring at a broken prompt.


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
