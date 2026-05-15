from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HouseViewSet, TagViewSet

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('', HouseViewSet, basename='houses')

urlpatterns = [
    path('', include(router.urls)),
]
