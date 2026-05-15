from django.urls import path, include

urlpatterns = [
    path('users/', include('apps.users.urls')),
    path('houses/', include('apps.houses.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('payments/', include('apps.payments.urls')),
    path('promos/', include('apps.promos.urls')),
]
