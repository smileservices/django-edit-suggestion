Usage
=====

It's attached to a model via a field that during django setup phase creates a model related to that specific parent model.

EditSuggestion instances:
- can be modified/deleted by the author of each instance
- status can be "under review", "rejected" and "published"
- status change need to pass a condition
- changing the status to "published" updates the tracked model and locks the edit suggestion from being edited/deleted

Parent Model Example
~~~~~~~~~~~~~~~~~~~~

Model has a field "edit_suggestion" that instantiates EditSuggestion
A serializer module and parent serializer is passed as a tuple ex:

.. code-block:: python

    def condition_check(user, parent_model_instance, edit_suggestion_instance):
        # do some checks and return a boolean
        if user.is_superuser or parent_model_instance.author == user:
            return True
        return False

    class ParentModel(models.Model):
        excluded_field = models.IntegerField()
        m2m_type_field = models.ManyToMany(Tags)
        edit_suggestions = EditSuggestion(
            excluded_fields=['excluded_field'],
            m2m_fields=({
                'name': 'm2m_type_field',
                'model': 'tags.models.Tags',
                'through': 'optional. empty if not used',
                }),
            change_status_condition=condition_check,
            bases=(VotableMixin,), # optional. bases are used to build the edit suggestion model upon them
            user_class=CustomUser, # optional. uses the default user model
        )

At django initializing stage the Edit Suggestion App creates a model for each Model having this field ex: "EditSuggestionParentModel"

Can access the model by ParentModel.edit_suggestions.model

How to use
~~~~~~~~~~


Create new edit suggestion
~~~~~~~~~~~~~~~~~~~~~~~~~~
After setting up the field inside the parent model just create a new edit suggestion by invoking the model ``create()`` method:

.. code-block:: python

    edit_suggestion = parentModelInstance.edit_suggestions.create(**user_data)


Diff against the parent
~~~~~~~~~~~~~~~~~~~~~~~
Can see the differences between the parent instance and the curent edit:

.. code-block:: python

    changes = edit_suggestion.diff_against_parent()



It will return an object ``ModelDelta`` that has the attributes:
- object.changes: tracked changes
- object.changed_fields: changed fields name
- object.old_record: parent instance
- object.new_record: current edit instance

Publish
~~~~~~~

To publish an edit suggestion you need to pass in an user. If the ``change_status_condition`` does not pass,
a ``django.contrib.auth.models.PermissionDenied`` exception will be raised.

.. code-block:: python

    edit_suggestion.publish(user)

This will change the status from ``edit_suggestion.Status.UNDER_REVIEWS`` to ``edit_suggestion.Status.PUBLISHED``.
After publishing, the edit suggestion won't be able to be edited anymore.

Reject
~~~~~~~

To reject an edit suggestion you need to pass in an user and a reason. If the ``change_status_condition`` does not pass,
a ``django.contrib.auth.models.PermissionDenied`` exception will be raised.

.. code-block:: python

    edit_suggestion.reject(user, reason)

This will change the status from ``edit_suggestion.Status.UNDER_REVIEWS`` to ``edit_suggestion.Status.REJECTED``.
After rejecting, the edit suggestion won't be able to be edited anymore.