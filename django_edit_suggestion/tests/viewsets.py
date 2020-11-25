from django_edit_suggestion.rest_views import ModelViewsetWithEditSuggestion
from .serializers import ParentSerializer, ParentEditSerializer


class ParentViewset(ModelViewsetWithEditSuggestion):
    serializer_class = ParentSerializer
    queryset = ParentSerializer.queryset
