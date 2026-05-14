from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'booking', 'amount', 'payment_type', 'status', 'created_at']
    list_filter = ['status', 'payment_type', 'created_at']
    search_fields = ['user__full_name', 'user__telegram_id', 'telegram_payment_id']
    readonly_fields = ['created_at', 'updated_at']
