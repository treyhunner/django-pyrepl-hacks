# Changelog


## 0.1.0 (2026-08-21)

Initial release.

- A `shell` management command that prefers the new Python REPL, with Django's auto-imported models and [pyrepl-hacks][] key bindings
- `PYREPL_BINDINGS` and `PYREPL_USE_DEFAULT_BINDINGS` for key bindings
- `PYREPL_THEME` for syntax highlighting colors (Python 3.14 and later)
- `PYREPL_SETUP` for anything else, including custom prompts and banners
- `manage.py shell --show-bindings` to see what is bound
- System checks for every setting

[pyrepl-hacks]: https://github.com/treyhunner/pyrepl-hacks
