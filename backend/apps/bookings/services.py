from __future__ import annotations

from decimal import Decimal
from datetime import date
from typing import Optional, List

from django.db import transaction
from django.core.exceptions import ValidationError

from apps.bookings.models import Booking
from apps.houses.models import House, Service
from apps.users.models import TelegramUser
from apps.promos.models import PromoCode


def calculate_booking_price(
    house: House,
    start_date: date,
    end_date: date,
    service_ids: List[int],
    user: TelegramUser,
    promo_code: Optional[PromoCode] = None,
) -> dict:

    days = (end_date - start_date).days
    base_price = Decimal(str(house.price_per_day)) * days

    services_cost = Decimal('0')
    services = Service.objects.filter(id__in=service_ids, house=house)
    for service in services:
        if service.is_daily:
            services_cost += service.price * days
        else:
            services_cost += service.price

    subtotal = base_price + services_cost


    discount_pct = Decimal('0')


    if user.referred_by and not user.new_user_discount_used:
        discount_pct = Decimal('25')

    elif user.discount_balance > 0:
        discount_pct = user.discount_balance


    if promo_code and promo_code.is_valid():
        promo_discount = promo_code.get_discount_amount(subtotal)
        if promo_code.discount_type == 'percent':
            if promo_code.value > discount_pct:
                discount_pct = Decimal(str(promo_code.value))
                promo_discount_amount = subtotal * discount_pct / 100
            else:
                promo_discount_amount = subtotal * discount_pct / 100
        else:

            discount_amount = promo_discount
            total_price = subtotal - discount_amount
            prepayment = (total_price * Decimal('0.10')).quantize(Decimal('0.01'))
            remaining = total_price - prepayment
            return {
                'base_price': base_price,
                'services_cost': services_cost,
                'subtotal': subtotal,
                'discount_pct': Decimal('0'),
                'discount_amount': discount_amount,
                'total_price': max(total_price, Decimal('0')),
                'prepayment_amount': prepayment,
                'remaining_amount': remaining,
                'days': days,
            }

    discount_amount = (subtotal * discount_pct / 100).quantize(Decimal('0.01'))
    total_price = subtotal - discount_amount
    prepayment = (total_price * Decimal('0.10')).quantize(Decimal('0.01'))
    remaining = total_price - prepayment

    return {
        'base_price': base_price,
        'services_cost': services_cost,
        'subtotal': subtotal,
        'discount_pct': discount_pct,
        'discount_amount': discount_amount,
        'total_price': max(total_price, Decimal('0')),
        'prepayment_amount': prepayment,
        'remaining_amount': remaining,
        'days': days,
    }


@transaction.atomic
def create_booking(
    user: TelegramUser,
    house_id: int,
    start_date: date,
    end_date: date,
    service_ids: List[int],
    promo_code_str: Optional[str] = None,
) -> Booking:

    house = House.objects.get(id=house_id, is_active=True)

    promo: Optional[PromoCode] = None
    if promo_code_str:
        try:
            promo = PromoCode.objects.get(code=promo_code_str, is_active=True)
            if not promo.is_valid():
                promo = None
        except PromoCode.DoesNotExist:
            pass

    pricing = calculate_booking_price(house, start_date, end_date, service_ids, user, promo)

    booking = Booking(
        user=user,
        house=house,
        start_date=start_date,
        end_date=end_date,
        status=Booking.Status.PENDING,
        total_price=pricing['total_price'],
        prepayment_amount=pricing['prepayment_amount'],
        remaining_amount=pricing['remaining_amount'],
        applied_discount=pricing['discount_pct'],
        promo_code=promo,
    )


    booking.clean()
    booking.save()

    if service_ids:
        services = Service.objects.filter(id__in=service_ids, house=house)
        booking.selected_services.set(services)

    if promo:
        promo.used_count += 1
        promo.save(update_fields=['used_count'])

    return booking


@transaction.atomic
def confirm_checkin(booking: Booking) -> Booking:
    if booking.status != Booking.Status.PARTIALLY_PAID:
        raise ValidationError('Заезд возможен только после внесения предоплаты.')
    booking.is_checked_in = True
    booking.save(update_fields=['is_checked_in', 'updated_at'])
    return booking


@transaction.atomic
def complete_booking_payment(booking: Booking) -> Booking:
    booking.status = Booking.Status.PAID
    booking.save(update_fields=['status', 'updated_at'])
    booking.generate_access_code()

    user = booking.user

    if user.referred_by and not user.new_user_discount_used:
        user.new_user_discount_used = True
        user.save(update_fields=['new_user_discount_used'])

    user.total_spent += booking.total_price
    user.total_bookings += 1
    user.save(update_fields=['total_spent', 'total_bookings'])

    from apps.users.services import apply_referral_discount_on_payment
    apply_referral_discount_on_payment(user)

    return booking


@transaction.atomic
def cancel_booking(booking: Booking, reason: str = '', by_admin: bool = False) -> Booking:
    if booking.status == Booking.Status.CANCELLED:
        raise ValidationError('Бронирование уже отменено.')
    if booking.status == Booking.Status.PAID and not by_admin:
        raise ValidationError('Нельзя отменить полностью оплаченное бронирование.')

    booking.status = Booking.Status.CANCELLED
    booking.cancel_reason = reason
    booking.save(update_fields=['status', 'cancel_reason', 'updated_at'])
    return booking
