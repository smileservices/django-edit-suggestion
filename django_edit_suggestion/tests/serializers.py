from .models import Tag, ParentModel, ParentM2MThroughModel, SharedChildOrder, SharedChild, ForeignKeyModel

from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django_edit_suggestion.rest_serializers import EditSuggestionSerializer


class TagSerializer(ModelSerializer):
    queryset = Tag.objects

    class Meta:
        model = Tag
        fields = ['name', ]


class ParentEditListingSerializer(ModelSerializer):
    queryset = ParentModel.edit_suggestions

    class Meta:
        model = ParentModel.edit_suggestions.model
        fields = ['pk', 'edit_suggestion_reason', 'edit_suggestion_author', 'edit_suggestion_date_created']


class ParentEditSerializer(ModelSerializer):
    queryset = ParentModel.edit_suggestions
    tags = TagSerializer(many=True)

    class Meta:
        model = ParentModel.edit_suggestions.model
        fields = ['pk', 'name', 'tags', 'edit_suggestion_reason', 'edit_suggestion_author']


class ParentSerializer(EditSuggestionSerializer):
    queryset = ParentModel.objects
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = ParentModel
        fields = ['name', 'tags']

    def run_validation(self, data):
        validated_data = super(ParentSerializer, self).run_validation(data)
        validated_data['tags'] = data['tags']
        return validated_data

    @staticmethod
    def get_edit_suggestion_serializer():
        return ParentEditSerializer

    @staticmethod
    def get_edit_suggestion_listing_serializer():
        return ParentEditListingSerializer


# serializers for model with foreign key
class SharedChildSerializer(ModelSerializer):
    queryset = SharedChild.objects.all()

    class Meta:
        model = SharedChild
        fields = ['name', 'pk']


class ForeignKeyEditSuggestionModelSerializer(ModelSerializer):
    queryset = ForeignKeyModel.edit_suggestions
    foreign = SharedChildSerializer(many=False, read_only=True)

    class Meta:
        model = ForeignKeyModel.edit_suggestions.model
        fields = ['name', 'foreign', 'pk', 'edit_suggestion_author']


class ForeignKeyModelSerializer(EditSuggestionSerializer):
    queryset = ForeignKeyModel.objects.all()
    foreign = SharedChildSerializer(many=False, read_only=True, allow_null=True)

    class Meta:
        model = ForeignKeyModel
        fields = ['name', 'foreign', 'pk']

    def run_validation(self, data):
        validated_data = super(ForeignKeyModelSerializer, self).run_validation(data)
        validated_data['foreign_id'] = data['foreign']
        return validated_data

    @staticmethod
    def get_edit_suggestion_serializer():
        return ForeignKeyEditSuggestionModelSerializer


# serializers for m2m through models
class HasChildrenFieldsSerializerMixin(ModelSerializer):
    children = SerializerMethodField()

    def get_children(self, obj):
        children = obj.children.through.objects.filter(parent=obj.pk).all()
        return [{'shared_child_id': child.pk, 'order': child.order} for child in children]


class ParentM2MThroughEditSerializer(HasChildrenFieldsSerializerMixin):
    queryset = ParentM2MThroughModel.edit_suggestions

    class Meta:
        model = ParentM2MThroughModel.edit_suggestions.model
        fields = ['pk', 'name', 'children', 'edit_suggestion_author']


class ParentM2MThroughSerializer(EditSuggestionSerializer, HasChildrenFieldsSerializerMixin):
    queryset = ParentM2MThroughModel.objects.all()

    class Meta:
        model = ParentM2MThroughModel
        fields = ['pk', 'name', 'children']

    def run_validation(self, data):
        validated_data = super(ParentM2MThroughSerializer, self).run_validation(data)
        validated_data['children'] = data['children']
        return validated_data

    @staticmethod
    def get_edit_suggestion_serializer():
        return ParentM2MThroughEditSerializer
