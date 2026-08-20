"""The settings the test suite runs under.

There is no Django project here, so this is the whole of it: enough to load
the app and run the checks.
"""

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_pyrepl_hacks",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

SECRET_KEY = "secret"

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
