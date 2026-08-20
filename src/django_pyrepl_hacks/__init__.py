"""A Django shell that uses the new Python REPL, with pyrepl-hacks key bindings.

Add ``"django_pyrepl_hacks"`` to ``INSTALLED_APPS`` and ``manage.py shell``
will launch the new Python REPL (``_pyrepl``) with Django's auto-imported
models and a set of extra key bindings.

Everything is configurable through ``PYREPL_*`` settings.
See the README for the full list.
"""

from .bindings import Insert, insert

__all__ = ["Insert", "insert"]
