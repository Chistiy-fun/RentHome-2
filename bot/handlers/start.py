import os
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

import services.api as api
from keyboards.keyboards import main_menu_keyboard

from dotenv import load_dotenv
load_dotenv()


router = Router()
logger = logging.getLogger(__name__)

BOT_USERNAME = os.getenv('BOT_USERNAME')


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    args = message.text.split(maxsplit=1)
    referral_code = None
    if len(args) > 1 and args[1].startswith('ref_'):
        referral_code = args[1][4:]

    user_data = await api.register_or_get_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or '',
        full_name=message.from_user.full_name,
        referral_code=referral_code,
    )

    if not user_data or 'error' in user_data:
        await message.answer('⚠️ Ошибка при регистрации. Попробуйте позже.')
        return

    # Greeting
    is_new = referral_code and not user_data.get('new_user_discount_used')
    greeting = f'👋 Привет, <b>{message.from_user.first_name}</b>!\n\n'

    if is_new:
        greeting += '🎁 Вы получили <b>скидку 25%</b> на первое бронирование!\n\n'

    greeting += (
        'Добро пожаловать в сервис аренды домов.\n'
        'Выберите действие в меню ниже:'
    )

    await message.answer(greeting, reply_markup=main_menu_keyboard(), parse_mode='HTML')


@router.message(Command('menu'))
@router.message(F.text == '◀️ Главное меню')
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer('Главное меню', reply_markup=main_menu_keyboard())


@router.message(Command('referral'))
@router.message(F.text == '🔗 Моя реферальная ссылка')
async def cmd_referral(message: Message) -> None:
    user = await api.get_user(message.from_user.id)
    if not user:
        await message.answer('Сначала запустите бота командой /start')
        return

    code = user['referral_code']
    link = f'https://t.me/{BOT_USERNAME}?start=ref_{code}'
    discount = user['discount_balance']
    referral_discount = user['referral_discount']

    text = (
        f'👥 <b>Реферальная программа</b>\n\n'
        f'Ваша ссылка:\n<code>{link}</code>\n\n'
        f'📊 Текущая скидка: <b>{referral_discount}%</b>\n'
        f'💎 Накопленная скидка: <b>{discount}%</b>\n\n'
        f'<i>Шкала скидок для рефереров:\n'
        f'1–2 приглашённых → 2%\n'
        f'3–5 → 5%\n'
        f'6–10 → 10%\n'
        f'10+ → 15%</i>'
    )
    await message.answer(text, parse_mode='HTML')
