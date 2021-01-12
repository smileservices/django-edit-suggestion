from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .viewsets import ParentViewset, ParentM2MThroughViewset, ForeignKeyModeViewset

router = DefaultRouter()
router.register('parent', ParentViewset, basename='parent-viewset')
router.register('m2m-through', ParentM2MThroughViewset, basename='m2m-through-viewset')
router.register('foreign', ForeignKeyModeViewset, basename='foreign-viewset')

urlpatterns = [
    path('api/', include(router.urls))
]