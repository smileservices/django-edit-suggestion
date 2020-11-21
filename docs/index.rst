.. django-edit-suggestion documentation master file, created by
   sphinx-quickstart on Mon Nov  9 13:24:09 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to "Django Edit Suggestion" documentation!
==================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   usage

About
~~~~~
A django package for enabling django resources to be edited by users other than admin or resource author.
The resource (an instance of a django model saved to database) will have a list of "edit suggestions" created by other users. The "edit suggestions" can be published,
which will update the resource, or can be rejected. Users that pass a condition can publish or reject edit suggestions.

Github Repo
~~~~~~~~~~~
https://github.com/smileservices/django-edit-suggestion


Changes
~~~~~~~
1.23:
- change status to Production/Stable
- add django_rest support with adding EditSuggestionSerializer and ModelViewsetWithEditSuggestion
