"""The app config, which exists to register the settings checks."""

from __future__ import annotations

from django.apps import AppConfig
from django.core.checks import register

from .checks import check_settings


class PyreplHacksConfig(AppConfig):
    name = "django_pyrepl_hacks"
    verbose_name = "Python REPL hacks"

    def ready(self) -> None:
        register(check_settings)
