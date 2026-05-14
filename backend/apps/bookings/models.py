"""
Booking model with date-blocking logic.
Status flow: pending → partially_paid → paid → (checked_in) → cancelled
"""

import random
import string
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError


def generate_access_code(length: int = 6) -> str:
    """Generate a 6-character alphanumeric access code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


class Booking(models.Model):
    """
    Rental booking. Dates are blocked immediately upon creation (status=pending).
    10% prepayment is required first; remaining paid on check-in.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает оплаты'
        PARTIALLY_PAID = 'partially_paid', 'Предоплата внесена'
        PAID = 'paid', 'Полностью оплачено'
        CANCELLED = 'cancelled', 'Отменено'

    user = models.ForeignKey(
        'users.TelegramUser', on_delete=models.CASCADE,
        related_name='bookings', verbose_name='Пользователь'
    )
    house = models.ForeignKey(
        'houses.House', on_delete=models.CASCADE,
        related_name='bookings', verbose_name='Дом'
    )
    start_date = models.DateField(verbose_name='Дата заезда')
    end_date = models.DateField(verbose_name='Дата выезда')
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.PENDING, verbose_name='Статус'
    )

    # Pricing
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Итоговая цена'
    )
    prepayment_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Предоплата (10%)'
    )
    remaining_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Остаток'
    )
    applied_discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name='Скидка (%)'
    )

    # Services
    selected_services = models.ManyToManyField(
        'houses.Service', blank=True, verbose_name='Выбранные услуги'
    )

    # Access
    access_code = models.CharField(
        max_length=10, blank=True, verbose_name='Код доступа'
    )
    is_checked_in = models.BooleanField(default=False, verbose_name='Заехал')

    # Cancellation
    cancel_reason = models.TextField(blank=True, verbose_name='Причина отмены')

    # Promo
    promo_code = models.ForeignKey(
        'promos.PromoCode', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Промокод'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'

    def __str__(self) -> str:
        return f'Бронь #{self.pk} | {self.user} | {self.house} | {self.start_date}–{self.end_date}'

    def clean(self) -> None:
        """Validate no overlapping bookings for the same house."""
        if self.start_date >= self.end_date:
            raise ValidationError('Дата выезда должна быть позже даты заезда.')

        overlapping = Booking.objects.filter(
            house=self.house,
            status__in=[self.Status.PENDING, self.Status.PARTIALLY_PAID, self.Status.PAID],
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError('Выбранные даты уже заняты. Пожалуйста, выберите другие даты.')

    def generate_access_code(self) -> str:
        """Generate and save access code. Called after full payment."""
        self.access_code = generate_access_code()
        self.save(update_fields=['access_code'])
        return self.access_code

    @property
    def days_count(self) -> int:
        return (self.end_date - self.start_date).days
