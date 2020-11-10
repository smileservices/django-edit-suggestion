from django.utils.deprecation import MiddlewareMixin

from .models import EditSuggestion


class EditSuggestionRequestMiddleware(MiddlewareMixin):
    """Expose request to EditableSuggestion.

    This middleware sets request as a local thread variable, making it
    available to the model-level utilities to allow tracking of the
    authenticated user making a change.
    """

    def process_request(self, request):
        EditSuggestion.thread.request = request

    def process_response(self, request, response):
        if hasattr(EditSuggestion.thread, "request"):
            del EditSuggestion.thread.request
        return response
