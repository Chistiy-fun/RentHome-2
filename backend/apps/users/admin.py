from django.contrib import admin
from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'full_name', 'username', 'total_spent',
                    'total_bookings', 'discount_balance', 'referral_code', 'created_at']
    search_fields = ['telegram_id', 'full_name', 'username', 'phone']
    list_filter = ['created_at']
    readonly_fields = ['referral_code', 'auth_token', 'total_spent',
                        'total_bookings', 'created_at']
