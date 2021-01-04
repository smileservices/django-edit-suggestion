from rest_framework.serializers import ModelSerializer


class EditSuggestionSerializer(ModelSerializer):

    @staticmethod
    def get_edit_suggestion_serializer():
        raise NotImplemented('EditSuggestionSerializer should implement get_edit_suggestion_serializer method!')

    @staticmethod
    def get_edit_suggestion_listing_serializer():
        raise NotImplemented('EditSuggestionSerializer should implement get_edit_suggestion_listing_serializer method!')
