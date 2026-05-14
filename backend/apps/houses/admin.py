from django.contrib import admin
from .models import House, HousePhoto, Service, Tag


class HousePhotoInline(admin.TabularInline):
    model = HousePhoto
    extra = 3


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['title', 'price_per_day', 'price_per_month', 'address',
                    'get_tags', 'is_active', 'date_created']
    list_filter = ['is_active', 'tags']
    search_fields = ['title', 'address', 'description']
    filter_horizontal = ['tags']
    inlines = [HousePhotoInline, ServiceInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['title', 'date_created']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'house', 'price', 'is_daily']
    list_filter = ['is_daily', 'house']
