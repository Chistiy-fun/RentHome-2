import asyncio
import logging
import os
from datetime import date, timedelta

from aiogram import Bot

import services.api as api

logger = logging.getLogger(__name__)

ADMIN_TG_ID = os.getenv('ADMIN_TELEGRAM_ID')


async def notify_user(bot: Bot, telegram_id: int, text: str) -> None:
    """ Отправка сообщения пользователю """
    try:
        await bot.send_message(chat_id=telegram_id, text=text, parse_mode='HTML')
    except Exception as e:
        logger.warning('Ошибка отправки сообщения %s: %s', telegram_id, e)


async def notify_admin(bot: Bot, text: str) -> None:
    """Forward a message to the admin."""
    if not ADMIN_TG_ID:
        return
    try:
        await bot.send_message(
            chat_id=int(ADMIN_TG_ID),
            text=f'[ADMIN]\n{text}',
            parse_mode='HTML',
        )
    except Exception as e:
        logger.warning('Failed to notify admin: %s', e)


async def send_booking_confirmation(bot: Bot, telegram_id: int, booking: dict) -> None:
    text = (
        f'✅ <b>Бронирование создано!</b>\n\n'
        f'🏠 Дом: {booking.get("house_title", "—")}\n'
        f'📅 Даты: {booking["start_date"]} — {booking["end_date"]}\n'
        f'💰 Итоговая цена: <b>{booking["total_price"]} ₽</b>\n'
        f'💳 К оплате сейчас (10%): <b>{booking["prepayment_amount"]} ₽</b>\n\n'
        f'Для подтверждения бронирования оплатите предоплату.'
    )
    await notify_user(bot, telegram_id, text)


async def send_prepayment_confirmation(bot: Bot, telegram_id: int, booking: dict) -> None:
    text = (
        f'✅ <b>Предоплата получена!</b>\n\n'
        f'🏠 {booking.get("house_title", "—")}\n'
        f'📅 {booking["start_date"]} — {booking["end_date"]}\n\n'
        f'Когда приедете — нажмите кнопку <b>"Я на месте"</b> в меню бронирований.'
    )
    await notify_user(bot, telegram_id, text)


async def send_full_payment_confirmation(bot: Bot, telegram_id: int, booking: dict) -> None:
    text = (
        f'🎉 <b>Оплата прошла успешно!</b>\n\n'
        f'🏠 {booking.get("house_title", "—")}\n'
        f'📅 {booking["start_date"]} — {booking["end_date"]}\n\n'
        f'🔑 Ваш код доступа: <b>{booking["access_code"]}</b>\n\n'
        f'Добро пожаловать!'
    )
    await notify_user(bot, telegram_id, text)


async def send_cancellation_notice(bot: Bot, telegram_id: int,
                                    booking: dict, reason: str = '') -> None:
    text = (
        f'❌ <b>Бронирование отменено</b>\n\n'
        f'🏠 {booking.get("house_title", "—")}\n'
        f'📅 {booking["start_date"]} — {booking["end_date"]}\n'
    )
    if reason:
        text += f'\nПричина: {reason}'
    await notify_user(bot, telegram_id, text)


# ── Напоминания БЕТА ────────────────────────────────────────────────────────

async def run_reminder_loop(bot_instance: Bot) -> None:
    backend_up = await api.wait_for_backend(retries=20, delay=3.0)
    if not backend_up:
        logger.error('Цикл прерван, сервер не доступен')
        return

    logger.info('Старт цикла напоминаний')
    while True:
        try:
            await _check_and_send_reminders(bot_instance)
        except Exception as e:
            logger.error('Ошибка цикла: %s', e)
        await asyncio.sleep(3600)


async def _check_and_send_reminders(bot_instance: Bot) -> None:
    tomorrow = (date.today() + timedelta(seconds=10)).isoformat()
    today = date.today().isoformat()

    page = 1
    while True:
        bookings_data = await api._get('/bookings/', params={'page': page})
        if not bookings_data or not isinstance(bookings_data, dict):
            break

        bookings = bookings_data.get('results', [])
        if not bookings:
            break

        for booking in bookings:
            if booking.get('status') not in ('pending', 'partially_paid'):
                continue

            start = booking.get('start_date', '')
            if start not in (tomorrow, today):
                continue

            detail = await api.get_booking(booking['id'])
            if not detail:
                continue

            user_data = await api._get(f'/users/{detail["user"]}/')
            if not user_data:
                continue
            tg_id = user_data.get('telegram_id')
            if not tg_id:
                continue

            house_title = booking.get('house_title', 'дом')

            if start == tomorrow:
                await notify_user(
                    bot_instance, tg_id,
                    f'⏰ <b>Напоминание:</b> завтра заезд в <b>{house_title}</b>!\n'
                    f'📅 {booking["start_date"]} — {booking["end_date"]}'
                )
            else:
                await notify_user(
                    bot_instance, tg_id,
                    f'⏰ <b>Напоминание:</b> сегодня ваш заезд в <b>{house_title}</b>!\n'
                    f'Не забудьте нажать <b>"Я на месте"</b> после приезда.'
                )

        if bookings_data.get('next'):
            page += 1
        else:
            break
