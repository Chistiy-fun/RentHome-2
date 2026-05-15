import logging
import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext

import services.api as api
from keyboards.keyboards import (
    booking_actions_keyboard, cancel_confirm_keyboard,
    checkin_pay_keyboard, main_menu_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


from dotenv import load_dotenv
load_dotenv()

PAYMENT_PROVIDER_TOKEN = os.getenv('TELEGRAM_PAYMENT_PROVIDER_TOKEN')
MOCK_PAYMENTS = os.environ.get('MOCK_PAYMENTS', 'true').lower() == 'true'

STATUS_EMOJI = {
    'pending': '⏳',
    'partially_paid': '💳',
    'paid': '✅',
    'cancelled': '❌',
}


# ── List bookings ─────────────────────────────────────────────────────────────

@router.message(F.text == '📖 Мои брони')
async def show_my_bookings(message: Message, state: FSMContext) -> None:
    await state.clear()
    bookings = await api.get_user_bookings(message.from_user.id)

    if not bookings:
        await message.answer('У вас нет бронирований.\n\nНажмите 🏠 Найти дом, чтобы забронировать!')
        return

    text = '📖 <b>Ваши бронирования:</b>\n\n'
    for b in bookings:
        emoji = STATUS_EMOJI.get(b['status'], '•')
        text += (
            f'{emoji} <b>{b.get("house_title", "Дом")}</b>\n'
            f'📅 {b["start_date"]} — {b["end_date"]}\n'
            f'💰 {b["total_price"]} ₽\n'
            f'/booking_{b["id"]}\n\n'
        )

    await message.answer(text, parse_mode='HTML')


@router.message(F.text.regexp(r'^/booking_(\d+)$'))
async def show_booking_detail(message: Message) -> None:
    booking_id = int(message.text.split('_')[1])
    await _show_booking(message, booking_id)


@router.callback_query(F.data.startswith('view_booking:'))
async def view_booking_callback(call: CallbackQuery) -> None:
    booking_id = int(call.data.split(':')[1])
    await call.answer()
    await _show_booking(call.message, booking_id)


async def _show_booking(message, booking_id: int) -> None:
    booking = await api.get_booking(booking_id)
    if not booking:
        await message.answer('Бронирование не найдено.')
        return

    emoji = STATUS_EMOJI.get(booking['status'], '•')
    services = booking.get('selected_services', [])
    svc_text = ', '.join(s['name'] for s in services) if services else 'нет'
    access = f'\n🔑 Код доступа: <b>{booking["access_code"]}</b>' if booking.get('access_code') else ''
    checkin_note = '\n✅ Отметился на месте' if booking.get('is_checked_in') else ''

    text = (
        f'{emoji} <b>Бронирование #{booking["id"]}</b>\n\n'
        f'🏠 {booking.get("house_title", "—")}\n'
        f'📅 {booking["start_date"]} — {booking["end_date"]} ({booking["days_count"]} дн.)\n'
        f'📊 Статус: {booking["status_display"]}\n'
        f'💰 Итого: {booking["total_price"]} ₽\n'
        f'💳 Предоплата: {booking["prepayment_amount"]} ₽\n'
        f'💳 Остаток: {booking["remaining_amount"]} ₽\n'
        f'🛠 Услуги: {svc_text}'
        f'{access}{checkin_note}'
    )

    if booking.get('cancel_reason'):
        text += f'\n\n❌ Причина отмены: {booking["cancel_reason"]}'

    kb = booking_actions_keyboard(booking)
    await message.answer(text, reply_markup=kb, parse_mode='HTML')


# ── Payments ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith('pay_prepayment:'))
async def pay_prepayment(call: CallbackQuery) -> None:
    booking_id = int(call.data.split(':')[1])
    booking = await api.get_booking(booking_id)
    if not booking:
        await call.answer('Бронирование не найдено', show_alert=True)
        return

    await call.answer()
    amount_kopecks = int(float(booking['prepayment_amount']) * 100)

    if MOCK_PAYMENTS or not PAYMENT_PROVIDER_TOKEN:
        # Mock payment — skip Telegram Payments, confirm directly
        result = await api.process_payment(
            booking_id=booking_id,
            telegram_id=call.from_user.id,
            payment_type='prepayment',
            telegram_payment_id='MOCK_PREPAYMENT',
        )
        await _handle_prepayment_result(call.message, call.from_user.id, result, booking)
    else:
        await call.message.answer_invoice(
            title=f'Предоплата за {booking.get("house_title", "дом")}',
            description=f'10% от стоимости аренды ({booking["start_date"]} — {booking["end_date"]})',
            payload=f'prepayment:{booking_id}',
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency='RUB',
            prices=[LabeledPrice(label='Предоплата (10%)', amount=amount_kopecks)],
        )


@router.callback_query(F.data.startswith('pay_remaining:'))
async def pay_remaining(call: CallbackQuery) -> None:
    booking_id = int(call.data.split(':')[1])
    booking = await api.get_booking(booking_id)
    if not booking:
        await call.answer('Бронирование не найдено', show_alert=True)
        return

    await call.answer()
    amount_kopecks = int(float(booking['remaining_amount']) * 100)

    if MOCK_PAYMENTS or not PAYMENT_PROVIDER_TOKEN:
        result = await api.process_payment(
            booking_id=booking_id,
            telegram_id=call.from_user.id,
            payment_type='full_payment',
            telegram_payment_id='MOCK_FULL_PAYMENT',
        )
        await _handle_full_payment_result(call.message, call.from_user.id, result)
    else:
        await call.message.answer_invoice(
            title=f'Оплата за {booking.get("house_title", "дом")}',
            description=f'Остаток оплаты ({booking["start_date"]} — {booking["end_date"]})',
            payload=f'full_payment:{booking_id}',
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency='RUB',
            prices=[LabeledPrice(label='Остаток оплаты', amount=amount_kopecks)],
        )


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message) -> None:
    payload = message.successful_payment.invoice_payload
    tg_payment_id = message.successful_payment.telegram_payment_charge_id

    parts = payload.split(':')
    payment_type = parts[0]
    booking_id = int(parts[1])

    result = await api.process_payment(
        booking_id=booking_id,
        telegram_id=message.from_user.id,
        payment_type=payment_type,
        telegram_payment_id=tg_payment_id,
    )

    if payment_type == 'prepayment':
        booking = await api.get_booking(booking_id)
        await _handle_prepayment_result(message, message.from_user.id, result, booking)
    else:
        await _handle_full_payment_result(message, message.from_user.id, result)


async def _handle_prepayment_result(message, tg_id: int, result: dict, booking: dict) -> None:
    if result and 'error' not in result:
        booking.update(result.get('payment', {}))
        await message.answer(
            f'✅ <b>Предоплата получена!</b>\n\n'
            f'Когда приедете — нажмите <b>"📍 Я на месте"</b>.',
            reply_markup=checkin_pay_keyboard(booking['id']),
            parse_mode='HTML'
        )
    else:
        err = result.get('error', 'Ошибка оплаты') if result else 'Ошибка'
        await message.answer(f'❌ {err}')


async def _handle_full_payment_result(message, tg_id: int, result: dict) -> None:
    if result and 'error' not in result:
        access_code = result.get('access_code', '—')
        await message.answer(
            f'🎉 <b>Оплата прошла успешно!</b>\n\n'
            f'🔑 Ваш код доступа: <code>{access_code}</code>\n\n'
            f'Добро пожаловать!',
            parse_mode='HTML'
        )
    else:
        err = result.get('error', 'Ошибка оплаты') if result else 'Ошибка'
        await message.answer(f'❌ {err}')


# ── Check-in ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith('checkin:'))
async def handle_checkin(call: CallbackQuery) -> None:
    booking_id = int(call.data.split(':')[1])
    await call.answer('Отмечаем...')

    result = await api.checkin_booking(booking_id)
    if result and 'error' not in result:
        await call.message.answer(
            '📍 Вы отметились на месте!\n\n'
            'Оплатите остаток, чтобы получить код доступа:',
            reply_markup=checkin_pay_keyboard(booking_id)
        )
    else:
        err = result.get('error', 'Ошибка') if result else 'Ошибка'
        await call.message.answer(f'❌ {err}')


# ── Cancellation ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith('cancel_booking:'))
async def ask_cancel_confirmation(call: CallbackQuery) -> None:
    booking_id = int(call.data.split(':')[1])
    await call.answer()
    await call.message.answer(
        '❓ Вы уверены, что хотите отменить бронирование?',
        reply_markup=cancel_confirm_keyboard(booking_id)
    )


@router.callback_query(F.data.startswith('confirm_cancel:'))
async def confirm_cancel(call: CallbackQuery) -> None:
    booking_id = int(call.data.split(':')[1])
    await call.answer('Отменяем...')

    result = await api.cancel_booking(booking_id, telegram_id=call.from_user.id)
    if result and 'error' not in result:
        await call.message.answer(
            '✅ Бронирование отменено. Даты освобождены.',
            reply_markup=main_menu_keyboard()
        )
    else:
        err = result.get('error', 'Ошибка') if result else 'Ошибка'
        await call.message.answer(f'❌ {err}')
