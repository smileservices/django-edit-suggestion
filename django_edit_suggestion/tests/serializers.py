from .models import Tag, ParentModel

from rest_framework.serializers import ModelSerializer
from django_edit_suggestion.rest_serializers import EditSuggestionSerializer


class TagSerializer(ModelSerializer):
    queryset = Tag.objects

    class Meta:
        model = Tag
        fields = ['name', ]


class ParentEditSerializer(ModelSerializer):
    queryset = ParentModel.edit_suggestions
    tags = TagSerializer(many=True)

    class Meta:
        model = ParentModel.edit_suggestions.model
        fields = ['name', 'tags', 'edit_suggestion_reason', 'edit_suggestion_author']


class ParentSerializer(EditSuggestionSerializer):
    queryset = ParentModel.objects
    tags = TagSerializer(many=True)

    class Meta:
        model = ParentModel
        fields = ['name', 'tags']

    @staticmethod
    def get_edit_suggestion_serializer():
        return ParentEditSerializer
