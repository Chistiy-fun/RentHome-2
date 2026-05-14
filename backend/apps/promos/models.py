"""Promo code model for discounts."""

from decimal import Decimal
from django.db import models
from django.utils import timezone


class PromoCode(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = 'percent', 'Процент'
        FIXED = 'fixed', 'Фиксированная сумма'

    code = models.CharField(max_length=32, unique=True, verbose_name='Код')
    discount_type = models.CharField(
        max_length=10, choices=DiscountType.choices,
        verbose_name='Тип скидки'
    )
    value = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name='Значение скидки'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Лимит использований'
    )
    used_count = models.PositiveIntegerField(default=0, verbose_name='Использован раз')
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name='Действует с')
    valid_to = models.DateTimeField(null=True, blank=True, verbose_name='Действует до')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'

    def __str__(self) -> str:
        return f'{self.code} ({self.get_discount_type_display()}: {self.value})'

    def is_valid(self) -> bool:
        """Check if promo is currently usable."""
        if not self.is_active:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

    def get_discount_amount(self, subtotal: Decimal) -> Decimal:
        """Return discount amount for a given subtotal."""
        if self.discount_type == self.DiscountType.PERCENT:
            return (subtotal * self.value / 100).quantize(Decimal('0.01'))
        return min(self.value, subtotal)
