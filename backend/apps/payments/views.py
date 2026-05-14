from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.bookings.models import Booking
from apps.users.models import TelegramUser
from .models import Payment
from .serializers import PaymentSerializer, ProcessPaymentSerializer
from .services import process_prepayment, process_full_payment


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Payments are created via /process endpoint, not directly via POST.
    Read-only list/retrieve for admin and bot history.
    """
    permission_classes = [AllowAny]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.select_related('user', 'booking')
        telegram_id = self.request.query_params.get('telegram_id')
        if telegram_id:
            qs = qs.filter(user__telegram_id=telegram_id)
        return qs

    @action(detail=False, methods=['post'], url_path='process')
    def process(self, request):
        """
        Bot calls this after receiving successful_payment update from Telegram.
        Handles both prepayment and full payment.
        """
        serializer = ProcessPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            booking = Booking.objects.get(id=d['booking_id'])
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        # Verify ownership
        if booking.user.telegram_id != d['telegram_id']:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        try:
            if d['payment_type'] == 'prepayment':
                payment = process_prepayment(
                    booking=booking,
                    telegram_payment_id=d.get('telegram_payment_id', ''),
                )
            else:
                payment = process_full_payment(
                    booking=booking,
                    telegram_payment_id=d.get('telegram_payment_id', ''),
                )
        except DjangoValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

        # Refresh booking for response
        booking.refresh_from_db()
        return Response({
            'payment': PaymentSerializer(payment).data,
            'booking_status': booking.status,
            'access_code': booking.access_code,
        })
