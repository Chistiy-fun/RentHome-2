from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import TelegramUser
from .serializers import TelegramUserSerializer, TelegramUserCreateSerializer
from .services import get_or_create_user


class TelegramUserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return TelegramUserCreateSerializer
        return TelegramUserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_or_get_user(request):

    telegram_id = request.data.get('telegram_id')
    username = request.data.get('username', '')
    full_name = request.data.get('full_name', '')
    referral_code = request.data.get('referral_code', None)

    if not telegram_id:
        return Response({'error': 'telegram_id required'}, status=status.HTTP_400_BAD_REQUEST)

    user, created = get_or_create_user(
        telegram_id=int(telegram_id),
        username=username,
        full_name=full_name,
    )

    if created and referral_code:
        from apps.users.models import TelegramUser as U
        try:
            referrer = U.objects.get(referral_code=referral_code)
            user.referred_by = referrer
            user.save(update_fields=['referred_by'])
        except U.DoesNotExist:
            pass

    serializer = TelegramUserSerializer(user)
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_by_telegram_id(request, telegram_id: int):
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return Response(TelegramUserSerializer(user).data)
    except TelegramUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
