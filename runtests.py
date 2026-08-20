#!/usr/bin/env python
"""Run the test suite without a Django project around it."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")


def runtests(labels):
    import django

    django.setup()
    from django.test.runner import DiscoverRunner

    failures = DiscoverRunner(failfast=False).run_tests(labels or ["tests"])
    sys.exit(failures)


if __name__ == "__main__":
    runtests(sys.argv[1:])
