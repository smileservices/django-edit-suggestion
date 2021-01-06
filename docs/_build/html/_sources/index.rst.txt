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
1.32
   #. rest_views: publish/reject edit suggestion: add success messages
1.31
   #. rest_views: use edit suggestion listing serializer when retrieving the list of edit suggestions

1.30
   #. add m2m through support in rest views and refactor the create edit suggestion

1.29
   #. add m2m through support

1.28
   #. ``edit_suggestions`` REST view returns paginated results. Can be filtered by status ex: ``api/resources/88/edit_suggestions/?status=0``

1.27
   #. Add post_publish/post_reject hooks

1.26
   #. REST viewset ``edit-suggestion-create`` returns serialized instance of edit suggestion

1.25
   #. add ``edit_suggestion_publish`` and ``edit_suggestion_reject`` to ``ModelViewsetWithEditSuggestion`` viewset
   #. create tests for them

1.24
   #. add m2m support to ``diff_against_parent``

1.23
   #. change status to Production/Stable
   #. add django_rest support with adding EditSuggestionSerializer and ModelViewsetWithEditSuggestion
