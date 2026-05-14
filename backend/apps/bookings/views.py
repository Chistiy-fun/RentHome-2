"""
Booking API views.
Bot sends telegram_id as identifier; backend resolves to TelegramUser.
"""

from __future__ import annotations

from typing import Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.users.models import TelegramUser
from apps.houses.models import House
from .models import Booking
from .serializers import (
    BookingListSerializer, BookingDetailSerializer,
    BookingCreateSerializer, PriceCalculateSerializer,
)
from .services import (
    create_booking, cancel_booking,
    confirm_checkin,
    calculate_booking_price,
)


def _get_user(telegram_id: int) -> Optional[TelegramUser]:
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Booking.objects.select_related('user', 'house').prefetch_related('selected_services')
        telegram_id = self.request.query_params.get('telegram_id')
        if telegram_id:
            qs = qs.filter(user__telegram_id=telegram_id)
        return qs

    def get_serializer_class(self):
        if self.action in ('list', ):
            return BookingListSerializer
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        user = _get_user(d['telegram_id'])
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            booking = create_booking(
                user=user,
                house_id=d['house_id'],
                start_date=d['start_date'],
                end_date=d['end_date'],
                service_ids=d.get('service_ids', []),
                promo_code_str=d.get('promo_code', ''),
            )
        except DjangoValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(BookingDetailSerializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='calculate-price')
    def calculate_price(self, request):
        """Preview price before creating booking."""
        serializer = PriceCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        user = _get_user(d['telegram_id'])
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            house = House.objects.get(id=d['house_id'], is_active=True)
        except House.DoesNotExist:
            return Response({'error': 'House not found'}, status=status.HTTP_404_NOT_FOUND)

        from apps.promos.models import PromoCode
        promo = None
        if d.get('promo_code'):
            try:
                promo = PromoCode.objects.get(code=d['promo_code'], is_active=True)
            except PromoCode.DoesNotExist:
                pass

        pricing = calculate_booking_price(
            house=house,
            start_date=d['start_date'],
            end_date=d['end_date'],
            service_ids=d.get('service_ids', []),
            user=user,
            promo_code=promo,
        )
        # Convert Decimals to str for JSON
        return Response({k: str(v) for k, v in pricing.items()})

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """User cancels their booking."""
        booking = self.get_object()
        telegram_id = request.data.get('telegram_id')
        reason = request.data.get('reason', '')

        if telegram_id and booking.user.telegram_id != int(telegram_id):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        try:
            booking = cancel_booking(booking, reason=reason)
        except DjangoValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(BookingDetailSerializer(booking).data)

    @action(detail=True, methods=['post'], url_path='admin-cancel')
    def admin_cancel(self, request, pk=None):
        """Admin cancels booking with reason (notifies user via bot)."""
        booking = self.get_object()
        reason = request.data.get('reason', 'Отменено администратором')

        try:
            booking = cancel_booking(booking, reason=reason, by_admin=True)
        except DjangoValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(BookingDetailSerializer(booking).data)

    @action(detail=True, methods=['post'], url_path='checkin')
    def checkin(self, request, pk=None):
        """User presses 'Я на месте' button."""
        booking = self.get_object()
        try:
            booking = confirm_checkin(booking)
        except DjangoValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BookingDetailSerializer(booking).data)
