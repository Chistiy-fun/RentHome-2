"""
Support: user message → forwarded to admin Telegram ID.
"""

import os
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from handlers.states import SupportStates
from keyboards.keyboards import main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)

ADMIN_TG_ID = os.environ.get('ADMIN_TELEGRAM_ID', '')


@router.message(F.text == 'ℹ️ Поддержка')
async def support_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        '💬 <b>Поддержка</b>\n\n'
        'Напишите ваш вопрос или проблему, и мы свяжемся с вами в ближайшее время.\n\n'
        '<i>Отправьте /menu для отмены</i>',
        parse_mode='HTML'
    )
    await state.set_state(SupportStates.waiting_message)


@router.message(SupportStates.waiting_message)
async def receive_support_message(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    await state.clear()

    # Forward to admin
    if ADMIN_TG_ID:
        try:
            admin_text = (
                f'📩 <b>Сообщение поддержки</b>\n\n'
                f'От: <b>{user.full_name}</b> (@{user.username or "нет"})\n'
                f'ID: <code>{user.id}</code>\n\n'
                f'Сообщение:\n{message.text}'
            )
            await bot.send_message(int(ADMIN_TG_ID), admin_text, parse_mode='HTML')
        except Exception as e:
            logger.error('Failed to forward to admin: %s', e)

    await message.answer(
        '✅ Ваше сообщение отправлено! Мы ответим вам в ближайшее время.',
        reply_markup=main_menu_keyboard()
    )
