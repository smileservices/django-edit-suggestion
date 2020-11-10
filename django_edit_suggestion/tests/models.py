from django.db import models
from django.contrib.auth.models import User
from django_edit_suggestion.models import EditSuggestion


class VotableMixin(models.Model):
    votes = models.IntegerField(default=0)

    class Meta:
        abstract = True


class Tag(models.Model):
    name = models.CharField(max_length=126)

    def __str__(self):
        return self.name


def condition_check(edit_suggestion_instance, user):
    # do some checks and return a boolean
    if user.is_staff:
        return True
    return False


class SimpleParentModel(models.Model):
    name = models.CharField(max_length=64)
    edit_suggestions = EditSuggestion(
        change_status_condition=condition_check,
    )

    def __str__(self):
        return self.name


class ParentModel(models.Model):
    name = models.CharField(max_length=64)
    excluded_field = models.IntegerField()
    tags = models.ManyToManyField(Tag)
    edit_suggestions = EditSuggestion(
        excluded_fields=['excluded_field'],
        m2m_fields=(({
                         'name': 'tags',
                         'model': Tag,
                     },)),
        change_status_condition=condition_check,
        bases=(VotableMixin,),  # optional. bases are used to build the edit suggestion model upon them
        user_model=User,  # optional. uses the default user model
    )

    def __str__(self):
        return self.name
