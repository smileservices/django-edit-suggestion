# Django Edit Suggestion

A django package for enabling django resources to be edited by users other than admin or resource author.
The resource (an instance of a django model saved to database) will have a list of "edit suggestions" created by other users. The "edit suggestions" can be published,
which will update the resource, or can be rejected. Users that pass a condition can publish or reject edit suggestions.

Documentation is available at [read the docs link](https://django-edit-suggestion.readthedocs.io/en/latest/).

## Install

Install from `PyPI` with ``pip``:

    $ pip install django-edit-suggestion


## Settings


Add ``django_edit_suggestion`` to your ``INSTALLED_APPS``

    INSTALLED_APPS = [
        # ...
        'django_edit_suggestion',
    ]

Requires to have Users
