from django_edit_suggestion.rest_views import ModelViewsetWithEditSuggestion
from .serializers import ParentSerializer, ParentEditSerializer, ParentM2MThroughSerializer, ForeignKeyModelSerializer


class ParentViewset(ModelViewsetWithEditSuggestion):
    serializer_class = ParentSerializer
    queryset = ParentSerializer.queryset


class ParentM2MThroughViewset(ModelViewsetWithEditSuggestion):
    serializer_class = ParentM2MThroughSerializer
    queryset = ParentM2MThroughSerializer.queryset


class ForeignKeyModeViewset(ModelViewsetWithEditSuggestion):
    serializer_class = ForeignKeyModelSerializer
    queryset = ForeignKeyModelSerializer.queryset


