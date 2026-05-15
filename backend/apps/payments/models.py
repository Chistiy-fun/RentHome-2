from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        PAID = 'paid', 'Оплачено'
        FAILED = 'failed', 'Ошибка'
        REFUNDED = 'refunded', 'Возврат'

    class PaymentType(models.TextChoices):
        PREPAYMENT = 'prepayment', 'Предоплата (10%)'
        FULL_PAYMENT = 'full_payment', 'Полная оплата'

    user = models.ForeignKey(
        'users.TelegramUser', on_delete=models.CASCADE,
        related_name='payments', verbose_name='Пользователь'
    )
    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.CASCADE,
        related_name='payments', verbose_name='Бронирование'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.PENDING, verbose_name='Статус'
    )
    payment_type = models.CharField(
        max_length=20, choices=PaymentType.choices,
        verbose_name='Тип платежа'
    )
    telegram_payment_id = models.CharField(
        max_length=128, blank=True, verbose_name='Telegram Payment ID'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'

    def __str__(self) -> str:
        return f'Платёж #{self.pk} | {self.get_payment_type_display()} | {self.amount} ₽ | {self.get_status_display()}'
