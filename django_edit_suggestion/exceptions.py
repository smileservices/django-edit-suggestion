"""
django-edit-suggestion exceptions and warnings classes.
"""


class MultipleRegistrationsError(Exception):
    """The model has been registered to have tracking more than once"""

    pass


class NoEditableSuggestionModelError(TypeError):
    """No related model found."""
    pass


class RelatedNameConflictError(Exception):
    """Related name conflicting with manager"""

    pass
