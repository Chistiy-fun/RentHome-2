from django.contrib import admin
from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'value', 'is_active',
                    'usage_limit', 'used_count', 'valid_from', 'valid_to']
    list_filter = ['is_active', 'discount_type']
    search_fields = ['code']
