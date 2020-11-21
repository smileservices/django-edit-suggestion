#!/usr/bin/env python
import logging
import sys
import django
from django.conf import settings
from django.test.runner import DiscoverRunner

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "rest_framework",

    "django_edit_suggestion",  # package to be tested
    "django_edit_suggestion.tests",  # test module to be run
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

DEFAULT_SETTINGS = dict(
    SECRET_KEY="not a secret",
    ALLOWED_HOSTS=["*"],
    INSTALLED_APPS=INSTALLED_APPS,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    MIDDLEWARE=MIDDLEWARE,
    ROOT_URLCONF = 'django_edit_suggestion.tests.urls',
    REST_FRAMEWORK={
        'TEST_REQUEST_DEFAULT_FORMAT': 'json'
    }
)




def main():
    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)
    django.setup()
    tags = [t.split("=")[1] for t in sys.argv if t.startswith("--tag")]
    failures = DiscoverRunner(failfast=False, tags=tags).run_tests(
        ["django_edit_suggestion.tests"]
    )
    sys.exit(failures)


if __name__ == "__main__":
    logging.basicConfig()
    main()
