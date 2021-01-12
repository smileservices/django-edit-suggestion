from __future__ import unicode_literals

import copy
import importlib
import threading
import warnings

import six
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.fields.proxy import OrderWrt
from django.forms.models import model_to_dict
from django.utils.text import format_lazy
from django.utils.encoding import smart_str
from . import exceptions
from .manager import EditSuggestionDescriptor
from django.contrib.auth.models import PermissionDenied
from django.db.models.fields.related import ForeignKey

registered_models = {}


class EditSuggestion(object):
    thread = threading.local()

    class Status(models.IntegerChoices):
        UNDER_REVIEWS = (0, 'under review')
        PUBLISHED = (1, 'published')
        REJECTED = (2, 'rejected')

    def __init__(
            self,
            change_status_condition,
            post_publish=None,
            post_reject=None,
            # m2m fields arg
            # tuple of dicts with keys 'name','model','through'-optional
            excluded_fields=None,
            m2m_fields=None,
            user_model=None,
            verbose_name=None,
            bases=(models.Model,),
            cascade_delete_edit_suggestion=False,
            custom_model_name=None,
            app=None,
            related_name=None,
    ):
        self.change_status_condition = change_status_condition
        self.post_publish = post_publish
        self.post_reject = post_reject
        self.user_set_verbose_name = verbose_name
        self.user_model = user_model
        self.m2m_fields = m2m_fields if m2m_fields else []
        self.cascade_delete_edit_suggestion = cascade_delete_edit_suggestion
        self.custom_model_name = custom_model_name
        self.app = app
        self.related_name = related_name
        self.excluded_fields = excluded_fields if excluded_fields else []
        self.edit_suggestion_model = None  # will be declared in finalize method
        self.tracked_fields = {'simple': [], 'foreign': [], 'm2m': []}  # filled up in set_tracked_fields method
        try:
            if isinstance(bases, six.string_types):
                raise TypeError
            self.bases = (EditSuggestionChanges,) + tuple(bases)
        except TypeError:
            raise TypeError("The `bases` option must be a list or a tuple.")

    def contribute_to_class(self, cls, name):
        self.manager_name = name
        self.module = cls.__module__
        self.cls = cls
        models.signals.class_prepared.connect(self.finalize, weak=False)

        if cls._meta.abstract:
            msg = (
                "EditSuggestion added to abstract model ({}) without "
                "inherit=True".format(self.cls.__name__)
            )
            warnings.warn(msg, UserWarning)

    def finalize(self, sender, **kwargs):
        # sender is the tracked_model
        self.parent_model_name = sender._meta.object_name
        if self.cls is not sender and not issubclass(sender, self.cls):
            return  # set in abstract

        if hasattr(sender._meta, "edit_suggestion_manager_attribute"):
            raise exceptions.MultipleRegistrationsError(
                "{}.{} registered multiple times for editable suggestion tracking.".format(
                    sender._meta.app_label, sender._meta.object_name
                )
            )
        # add pre_save listener check for editing status and handle publish
        self.edit_suggestion_model = self.create_edit_suggestion_model(sender)
        module = importlib.import_module(self.module)
        setattr(module, self.edit_suggestion_model.__name__, self.edit_suggestion_model)
        descriptor = EditSuggestionDescriptor(self.edit_suggestion_model)
        setattr(sender, self.manager_name, descriptor)
        sender._meta.edit_suggestion_manager_attribute = self.manager_name
        models.signals.pre_save.connect(self.pre_save_edit_suggestion, self.edit_suggestion_model, weak=False)

    def get_edit_suggestion_model_name(self, model):
        if not self.custom_model_name:
            return "EditSuggestion{}".format(model._meta.object_name)
        # Must be trying to use a custom edit_suggestion model name
        if callable(self.custom_model_name):
            name = self.custom_model_name(model._meta.object_name)
        else:
            #  simple string
            name = self.custom_model_name
        # Desired class name cannot be same as the model it is tracking
        if not (
                name.lower() == model._meta.object_name.lower()
                and model.__module__ == self.module
        ):
            return name
        raise ValueError(
            "The 'custom_model_name' option '{}' evaluates to a name that is the same "
            "as the model it is tracking. This is not permitted.".format(
                self.custom_model_name
            )
        )

    def set_tracked_fields(self, copied_fields):
        self.tracked_fields['m2m'] = [f for f in self.m2m_fields]
        for field_name, field in copied_fields.items():
            # exclude id and m2m fields
            if field_name == 'id' or field_name in [f['name'] for f in self.tracked_fields['m2m']]:
                continue
            if field.__class__ == ForeignKey:
                self.tracked_fields['foreign'].append(field_name)
            else :
                self.tracked_fields['simple'].append(field_name)

    def create_edit_suggestion_model(self, model):
        """
        Creates an editable suggestion model to associate with the model provided.
        """
        attrs = {
            "__module__": self.module,
            "_edit_suggestion_excluded_fields": self.excluded_fields,
        }

        app_module = "%s.models" % model._meta.app_label

        if model.__module__ != self.module:
            # registered under different app
            attrs["__module__"] = self.module
        elif app_module != self.module:
            # Abuse an internal API because the app registry is loading.
            app = apps.app_configs[model._meta.app_label]
            models_module = app.name
            attrs["__module__"] = models_module

        fields = {**self.copy_fields(model), **self.copy_m2m_fields(model)}
        self.set_tracked_fields(fields)
        attrs.update(fields)
        attrs.update(self.get_extra_fields(model, fields))
        # type in python2 wants str as a first argument
        attrs.update(Meta=type(str("Meta"), (), self.get_meta_options(model)))

        # Set as the default then check for overrides
        name = self.get_edit_suggestion_model_name(model)

        registered_models[model._meta.db_table] = model
        edit_suggestion_model = type(str(name), self.bases, attrs)
        return edit_suggestion_model

    def fields_included(self, model):
        fields = []
        for field in model._meta.fields:
            if field.name not in self.excluded_fields:
                fields.append(field)
        return fields

    def copy_fields(self, model):
        """
        Creates copies of the model's original fields, returning
        a dictionary mapping field name to copied field object.
        """
        fields = {}
        for field in self.fields_included(model):
            field = copy.copy(field)
            field.remote_field = copy.copy(field.remote_field)
            if isinstance(field, OrderWrt):
                # OrderWrt is a proxy field, switch to a plain IntegerField
                field.__class__ = models.IntegerField
            if isinstance(field, models.ForeignKey):
                old_field = field
                old_swappable = old_field.swappable
                old_field.swappable = False
                try:
                    _name, _path, args, field_args = old_field.deconstruct()
                finally:
                    old_field.swappable = old_swappable
                if getattr(old_field, "one_to_one", False) or isinstance(
                        old_field, models.OneToOneField
                ):
                    FieldType = models.ForeignKey
                else:
                    FieldType = type(old_field)

                # If field_args['to'] is 'self' then we have a case where the object
                # has a foreign key to itself. If we pass the edit suggestion record's
                # field to = 'self', the foreign key will point to an edit suggestion
                # record rather than the base record. We can use old_field.model here.
                if field_args.get("to", None) == "self":
                    field_args["to"] = old_field.model

                # Override certain arguments passed when creating the field
                # so that they work for the edit suggestion field.
                field_args.update(
                    db_constraint=False,
                    related_name="+",
                    null=True,
                    blank=True,
                    primary_key=False,
                    db_index=True,
                    serialize=True,
                    unique=False,
                    on_delete=models.DO_NOTHING,
                )
                field = FieldType(*args, **field_args)
                field.name = old_field.name
            else:
                transform_field(field)
            fields[field.name] = field
        return fields

    def copy_m2m_fields(self, model):
        # handle m2m fields
        fields = {}
        for m2m_field in self.m2m_fields:
            if type(m2m_field['model']) == str:
                if m2m_field['model'] == 'self':
                    m2m_field['model'] = model
                else:
                    m2m_field['model'] = __import__(m2m_field['model'])
            through = None
            if 'through' in m2m_field:
                # create new pivot table
                through = self.clone_pivot_table(model, m2m_field)
            fields[m2m_field['name']] = models.ManyToManyField(
                to=m2m_field['model'],
                through=through,
                related_name=self.get_related_name_for(m2m_field['name'])
            )
        return fields

    def clone_pivot_table(self, model, m2m_field):
        attrs = {
            "__module__": self.module,
        }

        app_module = "%s.models" % model._meta.app_label
        parent_model_name = self.get_edit_suggestion_model_name(model)

        if model.__module__ != self.module:
            # registered under different app
            attrs["__module__"] = self.module
        elif app_module != self.module:
            # Abuse an internal API because the app registry is loading.
            app = apps.app_configs[model._meta.app_label]
            models_module = app.name
            attrs["__module__"] = models_module

        fields = self.copy_fields(m2m_field['through']['model'])
        del fields['id']
        # add parent and relation fields
        field_args = dict(
            db_constraint=False,
            related_name="+",
            null=True,
            blank=True,
            primary_key=False,
            db_index=True,
            serialize=True,
            unique=False,
            on_delete=models.CASCADE,
        )
        fields[m2m_field['through']['self_field']] = models.ForeignKey(parent_model_name, **field_args)
        attrs.update(fields)

        name = self.get_edit_suggestion_model_name(m2m_field['through']['model'])
        edit_suggestion_through_model = type(str(name), (models.Model,), attrs)
        return edit_suggestion_through_model


    def get_extra_fields(self, model, fields):
        """
        Return dict of extra fields added to the edit suggestion record model
        """

        def str_repr(instance):
            return f'Edit Suggestion by {instance.edit_suggestion_author} for "{instance.edit_suggestion_parent}"'

        def publish(instance, user):
            # instance is the current edit suggestion
            if not self.change_status_condition(instance, user):
                raise PermissionDenied('User not allowed to publish the edit suggestion')
            for updatable_field in self.tracked_fields['simple']:
                setattr(instance.edit_suggestion_parent, updatable_field, getattr(instance, updatable_field))
            for updatable_field in self.tracked_fields['foreign']:
                setattr(instance.edit_suggestion_parent, updatable_field, getattr(instance, updatable_field))
            # set m2m fields
            for m2m_field in self.tracked_fields['m2m']:
                parent_m2m_field = getattr(instance.edit_suggestion_parent, m2m_field['name'])
                instance_m2m_field = getattr(instance, m2m_field['name'])
                if 'through' in m2m_field:
                    filter_dict = {}
                    filter_dict[m2m_field['through']['self_field']] = instance.edit_suggestion_parent
                    # need to filter manually

                    # clear the parent through records
                    parent_m2m_field.through.objects.filter(**filter_dict).all().delete()

                    # get supplimentary fields of through model
                    through_fields = []
                    for through_field in instance_m2m_field.through._meta.fields:
                        if through_field.name not in ['id', m2m_field['through']['self_field']]:
                            through_fields.append(through_field.name)

                    # need to filter manually
                    filter_dict[m2m_field['through']['self_field']] = instance
                    all_edit_through_children = instance_m2m_field.through.objects.filter(**filter_dict).all()

                    # copy child data of edit suggestion to parent by creating new children
                    for child in all_edit_through_children:
                        data = {
                            m2m_field['through']['self_field']: instance.edit_suggestion_parent
                        }
                        # populate extra through fields
                        for f in through_fields:
                            data[f] = getattr(child, f)
                        parent_m2m_field.through.objects.create(**data)
                else:
                    parent_m2m_field.set(instance_m2m_field.all())
            instance.edit_suggestion_parent.save()
            instance.edit_suggestion_status = self.Status.PUBLISHED
            instance.save()
            self.post_publish(instance, user) if self.post_publish else None

        def reject(instance, user, reason):
            if not self.change_status_condition(instance, user):
                raise PermissionDenied('User not allowed to reject the edit suggestion')
            instance.edit_suggestion_status = self.Status.REJECTED
            instance.edit_suggestion_reject_reason = reason
            instance.save()
            self.post_reject(instance, user, reason) if self.post_reject else None

        extra_fields = {
            "id": models.AutoField(primary_key=True),
            # edit suggestion author. if tracked model has a field with same name it should be excluded
            "edit_suggestion_author": models.ForeignKey(get_user_model(), null=True, blank=True,
                                                        on_delete=models.DO_NOTHING,
                                                        related_name=self.get_related_name_for("edit_suggestions")),
            # tracked model relationship
            "edit_suggestion_parent": models.ForeignKey(model, on_delete=models.CASCADE),
            "edit_suggestion_date_created": models.DateTimeField(auto_now_add=True),
            "edit_suggestion_date_updated": models.DateTimeField(auto_now=True),
            "edit_suggestion_reason": models.TextField(),
            "edit_suggestion_status": models.IntegerField(default=0, choices=self.Status.choices, db_index=True),
            "edit_suggestion_reject_reason": models.TextField(),
            "edit_suggestion_publish": publish,
            "edit_suggestion_reject": reject,
            "__str__": str_repr,
            "edit_suggestion_tracked_fields": self.tracked_fields,
        }

        return extra_fields

    def get_related_name_for(self, name):
        return f'{name}_{self.parent_model_name}'

    def get_meta_options(self, model):
        """
        Returns a dictionary of fields that will be added to
        the Meta inner class of the edit suggestion record model.
        """
        meta_fields = {
            "ordering": ("-edit_suggestion_date_created",),
            "get_latest_by": "edit_suggestion_date_created",
        }
        if self.user_set_verbose_name:
            name = self.user_set_verbose_name
        else:
            name = format_lazy("edit suggestion {}", smart_str(model._meta.verbose_name))
        meta_fields["verbose_name"] = name
        if self.app:
            meta_fields["app_label"] = self.app
        return meta_fields

    def pre_save_edit_suggestion(self, instance, raw, update_fields, using=None, **kwargs):
        # can edit only if the status is REVIEW
        try:
            from_db = self.edit_suggestion_model.objects.get(pk=instance.pk)
            if from_db.edit_suggestion_status != self.Status.UNDER_REVIEWS:
                raise PermissionDenied('Edit suggestion cannot be modified once the status changed')
        except self.edit_suggestion_model.DoesNotExist:
            pass


def transform_field(field):
    """Customize field appropriately for use in edit suggestion model"""
    field.name = field.attname
    if isinstance(field, models.BigAutoField):
        field.__class__ = models.BigIntegerField
    elif isinstance(field, models.AutoField):
        field.__class__ = models.IntegerField

    elif isinstance(field, models.FileField):
        # Don't copy file, just path.
        if getattr(settings, "EDIT_SUGGESTION_FILEFIELD_TO_CHARFIELD", False):
            field.__class__ = models.CharField
        else:
            field.__class__ = models.TextField

    #  instance shouldn't change create/update timestamps
    field.auto_now = False
    field.auto_now_add = False

    if field.primary_key or field.unique:
        # Unique fields can no longer be guaranteed unique,
        # but they should still be indexed for faster lookups.
        field.primary_key = False
        field._unique = False
        field.db_index = True
        field.serialize = True


class EditSuggestionChanges(object):
    '''
    should diff against the tracked model
    '''

    def diff_against_parent(self):
        changes = []
        changed_fields = []
        old_values = model_to_dict(self.edit_suggestion_parent)
        current_values = model_to_dict(self)
        for field in self.edit_suggestion_tracked_fields['simple'] + [f['name'] for f in self.edit_suggestion_tracked_fields['m2m']]:
            if field in old_values and old_values[field] != current_values[field]:
                change = ModelChange(field, old_values[field], current_values[field])
                changes.append(change)
                changed_fields.append(field)

        return ModelDelta(changes, changed_fields, self.edit_suggestion_parent, self)


class ModelChange(object):
    def __init__(self, field_name, old_value, new_value):
        self.field = field_name
        self.old = old_value
        self.new = new_value


class ModelDelta(object):
    def __init__(self, changes, changed_fields, old_record, new_record):
        self.changes = changes
        self.changed_fields = changed_fields
        self.old_record = old_record
        self.new_record = new_record
