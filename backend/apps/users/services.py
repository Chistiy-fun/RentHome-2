from __future__ import annotations

import secrets
from typing import Optional, Tuple

from apps.users.models import TelegramUser


def register_user(data: dict, referral_code: Optional[str] = None) -> TelegramUser:
    referrer: Optional[TelegramUser] = None
    if referral_code:
        try:
            referrer = TelegramUser.objects.get(referral_code=referral_code)
        except TelegramUser.DoesNotExist:
            pass

    token = secrets.token_hex(32)

    user = TelegramUser.objects.create(
        **data,
        referred_by=referrer,
        auth_token=token,
    )
    return user


def get_or_create_user(telegram_id: int, username: str, full_name: str) -> Tuple[TelegramUser, bool]:
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return user, False
    except TelegramUser.DoesNotExist:
        token = secrets.token_hex(32)
        user = TelegramUser.objects.create(
            telegram_id=telegram_id,
            username=username or '',
            full_name=full_name,
            auth_token=token,
        )
        return user, True


def apply_referral_discount_on_payment(user: TelegramUser) -> None:
    if not user.referred_by:
        return
    referrer = user.referred_by
    new_discount = referrer.get_referral_discount()
    referrer.discount_balance = new_discount
    referrer.save(update_fields=['discount_balance'])
