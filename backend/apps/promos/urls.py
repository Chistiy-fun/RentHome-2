from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PromoCodeViewSet

router = DefaultRouter()
router.register('', PromoCodeViewSet, basename='promos')

urlpatterns = [path('', include(router.urls))]
