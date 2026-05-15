from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'booking', 'amount', 'status', 'status_display',
            'payment_type', 'payment_type_display', 'telegram_payment_id',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProcessPaymentSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    payment_type = serializers.ChoiceField(choices=['prepayment', 'full_payment'])
    telegram_payment_id = serializers.CharField(required=False, allow_blank=True)
    telegram_id = serializers.IntegerField()
