from django.db import transaction
from django.core.exceptions import ValidationError

from apps.payments.models import Payment
from apps.bookings.models import Booking


@transaction.atomic
def process_prepayment(booking: Booking, telegram_payment_id: str = '') -> Payment:
    if booking.status != Booking.Status.PENDING:
        raise ValidationError('Предоплата уже была внесена или бронирование недоступно.')

    existing = Payment.objects.filter(
        booking=booking,
        payment_type=Payment.PaymentType.PREPAYMENT,
        status=Payment.Status.PAID,
    ).exists()
    if existing:
        raise ValidationError('Предоплата уже была произведена.')

    payment = Payment.objects.create(
        user=booking.user,
        booking=booking,
        amount=booking.prepayment_amount,
        status=Payment.Status.PAID,
        payment_type=Payment.PaymentType.PREPAYMENT,
        telegram_payment_id=telegram_payment_id,
    )

    booking.status = Booking.Status.PARTIALLY_PAID
    booking.save(update_fields=['status', 'updated_at'])

    return payment


@transaction.atomic
def process_full_payment(booking: Booking, telegram_payment_id: str = '') -> Payment:
    if booking.status != Booking.Status.PARTIALLY_PAID:
        raise ValidationError('Бронирование должно быть в статусе "предоплата внесена".')
    if not booking.is_checked_in:
        raise ValidationError('Пользователь ещё не отметился на месте.')

    existing = Payment.objects.filter(
        booking=booking,
        payment_type=Payment.PaymentType.FULL_PAYMENT,
        status=Payment.Status.PAID,
    ).exists()
    if existing:
        raise ValidationError('Полная оплата уже была произведена.')

    payment = Payment.objects.create(
        user=booking.user,
        booking=booking,
        amount=booking.remaining_amount,
        status=Payment.Status.PAID,
        payment_type=Payment.PaymentType.FULL_PAYMENT,
        telegram_payment_id=telegram_payment_id,
    )

    from apps.bookings.services import complete_booking_payment
    complete_booking_payment(booking)

    return payment


def create_pending_payment(booking: Booking, payment_type: str) -> Payment:
    amount = (
        booking.prepayment_amount
        if payment_type == Payment.PaymentType.PREPAYMENT
        else booking.remaining_amount
    )
    return Payment.objects.create(
        user=booking.user,
        booking=booking,
        amount=amount,
        status=Payment.Status.PENDING,
        payment_type=payment_type,
    )
