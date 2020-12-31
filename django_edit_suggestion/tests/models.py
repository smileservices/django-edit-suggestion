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


def post_publish(instance, user):
    user.username = 'published'
    user.save()


def post_reject(instance, user, reason):
    user.username = 'rejected'
    user.save()


class SimpleParentModel(models.Model):
    name = models.CharField(max_length=64)
    edit_suggestions = EditSuggestion(
        change_status_condition=condition_check,
        post_publish=post_publish,
        post_reject=post_reject,
    )

    def __str__(self):
        return self.name


class ParentModel(models.Model):
    name = models.CharField(max_length=64)
    second_field = models.CharField(max_length=64, blank=True, null=True)
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


class ParentM2MSelfModel(models.Model):
    name = models.CharField(max_length=64)
    children = models.ManyToManyField('ParentM2MSelfModel')
    edit_suggestions = EditSuggestion(
        m2m_fields=(({
                         'name': 'children',
                         'model': 'self',
                     },)),
        change_status_condition=condition_check,
        bases=(VotableMixin,),  # optional. bases are used to build the edit suggestion model upon them
        user_model=User,  # optional. uses the default user model
    )

    def __str__(self):
        return self.name


class SharedChild(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class SharedChildOrder(models.Model):
    parent = models.ForeignKey('ParentM2MThroughModel', on_delete=models.CASCADE)
    shared_child = models.ForeignKey(SharedChild, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)


class ParentM2MThroughModel(models.Model):
    name = models.CharField(max_length=64)
    children = models.ManyToManyField(SharedChild, through=SharedChildOrder)
    edit_suggestions = EditSuggestion(
        m2m_fields=(({
                         'name': 'children',
                         'model': SharedChild,
                         'through': {
                             'model': SharedChildOrder,
                             'self_field': 'parent',
                         },
                     },)),
        change_status_condition=condition_check,
        bases=(VotableMixin,),  # optional. bases are used to build the edit suggestion model upon them
        user_model=User,  # optional. uses the default user model
    )

    def __str__(self):
        return self.name
