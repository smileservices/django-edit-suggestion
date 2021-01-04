from .models import Tag, ParentModel, ParentM2MThroughModel, SharedChildOrder, SharedChild

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
    tags = TagSerializer(many=True)

    class Meta:
        model = ParentModel
        fields = ['name', 'tags']

    @staticmethod
    def get_edit_suggestion_serializer():
        return ParentEditSerializer

    @staticmethod
    def get_edit_suggestion_listing_serializer():
        return ParentEditListingSerializer


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

    @staticmethod
    def get_edit_suggestion_serializer():
        return ParentM2MThroughEditSerializer
