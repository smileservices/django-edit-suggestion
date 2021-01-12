from __future__ import unicode_literals

from django.db import models


class EditSuggestionDescriptor(object):

    def __init__(self, model):
        self.model = model

    def __get__(self, instance, owner):
        if instance is None:
            return EditSuggestionManager(self.model)
        return EditSuggestionManager(self.model, instance)


class EditSuggestionManager(models.Manager):

    def __init__(self, model, instance=None):
        super(EditSuggestionManager, self).__init__()
        self.model = model
        self.instance = instance

    def get_super_queryset(self):
        return super(EditSuggestionManager, self).get_queryset()

    def get_queryset(self):
        qs = self.get_super_queryset()
        if self.instance is None:
            return qs
        return self.get_super_queryset().filter(**{'edit_suggestion_parent': self.instance})

    def new(self, data):
        data['edit_suggestion_parent'] = self.instance
        return self.create(**data)

    def get_tracked_fields(self):
        return self.model.edit_suggestion_tracked_fields['simple'],  self.model.edit_suggestion_tracked_fields['foreign'], self.model.edit_suggestion_tracked_fields['m2m']
