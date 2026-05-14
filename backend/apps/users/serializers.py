from rest_framework import serializers
from .models import TelegramUser


class TelegramUserSerializer(serializers.ModelSerializer):
    referral_discount = serializers.SerializerMethodField()

    class Meta:
        model = TelegramUser
        fields = [
            'id', 'telegram_id', 'username', 'full_name', 'phone',
            'total_spent', 'total_bookings', 'discount_balance',
            'referral_code', 'referred_by', 'new_user_discount_used',
            'auth_token', 'referral_discount', 'created_at',
        ]
        read_only_fields = ['referral_code', 'auth_token', 'total_spent',
                             'total_bookings', 'created_at']

    def get_referral_discount(self, obj: TelegramUser) -> int:
        return obj.get_referral_discount()


class TelegramUserCreateSerializer(serializers.ModelSerializer):
    """Used by bot when registering a new user via /start."""

    referral_code_used = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = TelegramUser
        fields = ['telegram_id', 'username', 'full_name', 'phone', 'referral_code_used']

    def create(self, validated_data: dict) -> TelegramUser:
        from apps.users.services import register_user
        ref_code = validated_data.pop('referral_code_used', None)
        return register_user(validated_data, ref_code)
