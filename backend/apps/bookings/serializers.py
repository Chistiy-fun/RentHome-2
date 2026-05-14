from datetime import date
from rest_framework import serializers

from apps.houses.serializers import ServiceSerializer
from .models import Booking


class BookingListSerializer(serializers.ModelSerializer):
    house_title = serializers.CharField(source='house.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'house', 'house_title', 'start_date', 'end_date',
            'status', 'status_display', 'total_price', 'prepayment_amount',
            'remaining_amount', 'is_checked_in', 'access_code', 'created_at',
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    house_title = serializers.CharField(source='house.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    selected_services = ServiceSerializer(many=True, read_only=True)
    days_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'house', 'house_title', 'start_date', 'end_date',
            'status', 'status_display', 'total_price', 'prepayment_amount',
            'remaining_amount', 'applied_discount', 'selected_services',
            'access_code', 'is_checked_in', 'cancel_reason', 'days_count',
            'created_at', 'updated_at',
        ]


class BookingCreateSerializer(serializers.Serializer):
    """Input for creating a booking from the bot."""
    house_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    service_ids = serializers.ListField(child=serializers.IntegerField(), default=list)
    promo_code = serializers.CharField(required=False, allow_blank=True)
    telegram_id = serializers.IntegerField()

    def validate(self, attrs):
        if attrs['start_date'] >= attrs['end_date']:
            raise serializers.ValidationError('Дата выезда должна быть позже даты заезда.')
        if attrs['start_date'] < date.today():
            raise serializers.ValidationError('Нельзя бронировать прошедшие даты.')
        return attrs


class PriceCalculateSerializer(serializers.Serializer):
    """For price preview before booking confirmation."""
    house_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    service_ids = serializers.ListField(child=serializers.IntegerField(), default=list)
    promo_code = serializers.CharField(required=False, allow_blank=True)
    telegram_id = serializers.IntegerField()
