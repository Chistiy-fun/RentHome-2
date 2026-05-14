from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.TelegramUserViewSet, basename='users')

urlpatterns = [
    path('register/', views.register_or_get_user, name='user-register'),
    path('by-telegram-id/<int:telegram_id>/', views.get_user_by_telegram_id, name='user-by-tg-id'),
    path('', include(router.urls)),
]
