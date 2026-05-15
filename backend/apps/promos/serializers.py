from rest_framework import serializers
from .models import PromoCode


class PromoCodeSerializer(serializers.ModelSerializer):
    is_valid_now = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'discount_type', 'value', 'is_active',
            'usage_limit', 'used_count', 'valid_from', 'valid_to',
            'is_valid_now', 'created_at',
        ]

    def get_is_valid_now(self, obj: PromoCode) -> bool:
        return obj.is_valid()


class PromoCheckSerializer(serializers.Serializer):
    code = serializers.CharField()
