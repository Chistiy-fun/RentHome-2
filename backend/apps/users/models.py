import uuid
from django.db import models


def generate_referral_code() -> str:
    return uuid.uuid4().hex[:8].upper()


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=64, blank=True, verbose_name='Username')
    full_name = models.CharField(max_length=128, verbose_name='Полное имя')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')

    total_spent = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Всего потрачено'
    )
    total_bookings = models.PositiveIntegerField(default=0, verbose_name='Всего бронирований')
    discount_balance = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Накопительная скидка (%)'
    )

    referral_code = models.CharField(
        max_length=16, unique=True, default=generate_referral_code,
        verbose_name='Реферальный код'
    )
    referred_by = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='referrals',
        verbose_name='Приглашён пользователем'
    )
    new_user_discount_used = models.BooleanField(
        default=False, verbose_name='Использовал стартовую скидку'
    )

    auth_token = models.CharField(max_length=64, blank=True, verbose_name='API токен')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return f'{self.full_name} (@{self.username})'

    def get_referral_discount(self) -> int:
        count = self.referrals.count()
        if count >= 10:
            return 15
        elif count >= 6:
            return 10
        elif count >= 3:
            return 5
        elif count >= 1:
            return 2
        return 0
