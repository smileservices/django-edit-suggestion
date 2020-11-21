from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .viewsets import ParentViewset

router = DefaultRouter()
router.register('parent', ParentViewset, basename='parent-viewset')

urlpatterns = [
    path('api/', include(router.urls))
]