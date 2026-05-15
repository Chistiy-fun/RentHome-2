from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import PromoCode
from .serializers import PromoCodeSerializer, PromoCheckSerializer


class PromoCodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='check')
    def check(self, request):
        serializer = PromoCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']

        try:
            promo = PromoCode.objects.get(code=code, is_active=True)
        except PromoCode.DoesNotExist:
            return Response({'valid': False, 'error': 'Промокод не найден'})

        if not promo.is_valid():
            return Response({'valid': False, 'error': 'Промокод недействителен или истёк'})

        return Response({
            'valid': True,
            'discount_type': promo.discount_type,
            'value': str(promo.value),
        })
