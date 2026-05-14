from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import House, Service, Tag
from .serializers import (
    HouseListSerializer, HouseDetailSerializer,
    ServiceSerializer, TagSerializer
)


class HouseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Houses are read-only via API (managed through Django Admin).
    Bot only needs to list and retrieve.
    """
    queryset = House.objects.filter(is_active=True).prefetch_related('tags', 'photos', 'services')
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'address', 'description']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return HouseDetailSerializer
        return HouseListSerializer

    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        """Get all services for a specific house."""
        house = self.get_object()
        services = house.services.all()
        return Response(ServiceSerializer(services, many=True).data)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Return booked date ranges for this house.
        Bot uses this to block unavailable dates in calendar.
        """
        from apps.bookings.models import Booking
        house = self.get_object()
        bookings = Booking.objects.filter(
            house=house,
            status__in=['pending', 'partially_paid', 'paid']
        ).values('start_date', 'end_date')
        return Response(list(bookings))


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
