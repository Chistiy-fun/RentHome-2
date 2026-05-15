from django.contrib import admin
from django.utils.html import format_html
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'house', 'start_date', 'end_date',
        'colored_status', 'total_price', 'access_code', 'is_checked_in', 'created_at'
    ]
    list_filter = ['status', 'is_checked_in', 'house', 'created_at']
    search_fields = ['user__full_name', 'user__telegram_id', 'house__title', 'access_code']
    readonly_fields = ['access_code', 'total_price', 'prepayment_amount',
                       'remaining_amount', 'created_at', 'updated_at']
    filter_horizontal = ['selected_services']
    actions = ['admin_cancel_bookings']

    def colored_status(self, obj):
        colors = {
            'pending': '#f0ad4e',
            'partially_paid': '#5bc0de',
            'paid': '#5cb85c',
            'cancelled': '#d9534f',
        }
        color = colors.get(obj.status, '#777')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    colored_status.short_description = 'Статус'

    def admin_cancel_bookings(self, request, queryset):
        from apps.bookings.services import cancel_booking
        cancelled = 0
        for booking in queryset.exclude(status='cancelled'):
            try:
                cancel_booking(booking, reason='Отменено администратором', by_admin=True)
                cancelled += 1
            except Exception:
                pass
        self.message_user(request, f'Отменено бронирований: {cancelled}')
    admin_cancel_bookings.short_description = 'Отменить выбранные бронирования'
