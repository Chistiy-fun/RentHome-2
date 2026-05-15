import logging
import math
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import services.api as api
from handlers.states import BookingStates
from keyboards.keyboards import (
    houses_navigation_keyboard, house_card_keyboard,
    services_keyboard, promo_keyboard, confirm_booking_keyboard,
    main_menu_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)

PAGE_SIZE = 5


# ── House list ────────────────────────────────────────────────────────────────

@router.message(F.text == '🏠 Найти дом')
async def show_houses(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_houses_page(message, page=1)


@router.callback_query(F.data.startswith('houses_page:'))
async def paginate_houses(call: CallbackQuery) -> None:
    page = int(call.data.split(':')[1])
    await call.answer()
    await _send_houses_page(call.message, page=page, edit=True)


async def _send_houses_page(message, page: int, edit: bool = False) -> None:
    data = await api.get_houses(page=page)
    if not data:
        await message.answer('Дома не найдены. Попробуйте позже.')
        return

    results = data.get('results', [])
    count = data.get('count', 0)
    total_pages = max(1, math.ceil(count / PAGE_SIZE))

    if not results:
        await message.answer('Список домов пуст.')
        return

    text = f'🏠 <b>Доступные дома</b> (стр. {page}/{total_pages})\n\n'
    for h in results:
        text += (
            f'<b>{h["title"]}</b>\n'
            f'📍 {h["address"]}\n'
            f'💰 {h["price_per_day"]} ₽/сутки | {h["price_per_month"]} ₽/месяц\n'
            f'/house_{h["id"]}\n\n'
        )

    kb = houses_navigation_keyboard(page, total_pages)
    if edit:
        await message.edit_text(text, reply_markup=kb, parse_mode='HTML')
    else:
        await message.answer(text, reply_markup=kb, parse_mode='HTML')


@router.message(F.text.regexp(r'^/house_(\d+)$'))
async def show_house_card(message: Message) -> None:
    house_id = int(message.text.split('_')[1])
    await _show_house(message, house_id)


@router.callback_query(F.data.startswith('book_house:'))
async def start_booking_from_card(call: CallbackQuery, state: FSMContext) -> None:
    house_id = int(call.data.split(':')[1])
    await call.answer()
    await state.update_data(house_id=house_id, service_ids=[])
    await call.message.answer(
        '📅 Введите <b>дату заезда</b> в формате ДД.ММ.ГГГГ\n'
        'Например: <code>15.06.2025</code>',
        parse_mode='HTML'
    )
    await state.set_state(BookingStates.waiting_start_date)


async def _show_house(message, house_id: int) -> None:
    house = await api.get_house(house_id)
    if not house:
        await message.answer('Дом не найден.')
        return

    tags = ', '.join(t['title'] for t in house.get('tags', [])) or '—'
    services = house.get('services', [])
    svc_text = ''
    for s in services:
        daily = ' (×дни)' if s['is_daily'] else ''
        svc_text += f'\n  • {s["name"]} — {s["price"]} ₽{daily}'

    text = (
        f'🏠 <b>{house["title"]}</b>\n\n'
        f'📍 {house["address"]}\n'
        f'💰 {house["price_per_day"]} ₽/сутки | {house["price_per_month"]} ₽/месяц\n\n'
        f'📝 {house["description"]}\n\n'
        f'✨ Удобства: {tags}'
    )
    if svc_text:
        text += f'\n\n🛠 Дополнительные услуги:{svc_text}'

    photos = house.get('photos', [])
    kb = house_card_keyboard(house_id)

    if photos:
        try:
            await message.answer_photo(
                photo=photos[0]['image'],
                caption=text,
                reply_markup=kb,
                parse_mode='HTML'
            )
        except Exception as e:
            await message.answer(text, reply_markup=kb, parse_mode='HTML')
            print(e)

    else:
        await message.answer(text, reply_markup=kb, parse_mode='HTML')


# ── Booking ──────────────────────────────────────────────────────────

@router.message(BookingStates.waiting_start_date)
async def receive_start_date(message: Message, state: FSMContext) -> None:
    try:
        dt = datetime.strptime(message.text.strip(), '%d.%m.%Y')
        if dt.date() < datetime.today().date():
            await message.answer('❌ Дата не может быть в прошлом. Введите другую дату:')
            return
    except ValueError:
        await message.answer('❌ Неверный формат. Введите дату как <code>15.06.2025</code>:', parse_mode='HTML')
        return

    await state.update_data(start_date=dt.strftime('%Y-%m-%d'))
    await message.answer(
        '📅 Введите <b>дату выезда</b> в формате ДД.ММ.ГГГГ:',
        parse_mode='HTML'
    )
    await state.set_state(BookingStates.waiting_end_date)


@router.message(BookingStates.waiting_end_date)
async def receive_end_date(message: Message, state: FSMContext) -> None:
    try:
        dt = datetime.strptime(message.text.strip(), '%d.%m.%Y')
    except ValueError:
        await message.answer('❌ Неверный формат. Введите дату как <code>15.06.2025</code>:', parse_mode='HTML')
        return

    data = await state.get_data()
    start = datetime.strptime(data['start_date'], '%Y-%m-%d').date()

    if dt.date() <= start:
        await message.answer('❌ Дата выезда должна быть позже даты заезда.')
        return

    await state.update_data(end_date=dt.strftime('%Y-%m-%d'))

    house = await api.get_house(data['house_id'])
    services = house.get('services', []) if house else []

    if services:
        await state.update_data(available_services=services)
        await message.answer(
            '🛠 Выберите дополнительные услуги (нажмите для выбора):',
            reply_markup=services_keyboard(services, selected_ids=[])
        )
        await state.set_state(BookingStates.selecting_services)
    else:
        await state.update_data(service_ids=[])
        await _ask_promo(message, state)


@router.callback_query(BookingStates.selecting_services, F.data.startswith('toggle_service:'))
async def toggle_service(call: CallbackQuery, state: FSMContext) -> None:
    svc_id = int(call.data.split(':')[1])
    data = await state.get_data()
    selected = list(data.get('service_ids', []))

    if svc_id in selected:
        selected.remove(svc_id)
    else:
        selected.append(svc_id)

    await state.update_data(service_ids=selected)
    await call.message.edit_reply_markup(
        reply_markup=services_keyboard(data['available_services'], selected)
    )
    await call.answer()


@router.callback_query(BookingStates.selecting_services, F.data.in_({'services_done', 'services_skip'}))
async def services_confirmed(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.data == 'services_skip':
        await state.update_data(service_ids=[])
    await _ask_promo(call.message, state)


async def _ask_promo(message, state: FSMContext) -> None:
    await message.answer('🎟 У вас есть промокод?', reply_markup=promo_keyboard())
    await state.set_state(BookingStates.waiting_promo)


@router.callback_query(BookingStates.waiting_promo, F.data == 'enter_promo')
async def ask_promo_input(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await call.message.answer('Введите промокод:')


@router.message(BookingStates.waiting_promo)
async def receive_promo(message: Message, state: FSMContext) -> None:
    code = message.text.strip().upper()
    result = await api.check_promo(code)
    if result and result.get('valid'):
        await state.update_data(promo_code=code)
        await message.answer(
            f'✅ Промокод принят! Скидка: <b>{result["value"]}'
            f'{"%" if result["discount_type"] == "percent" else " ₽"}</b>',
            parse_mode='HTML'
        )
    else:
        err = result.get('error', 'Промокод недействителен') if result else 'Ошибка'
        await message.answer(f'❌ {err}')
        await state.update_data(promo_code='')
    await _show_price_summary(message, state)


@router.callback_query(BookingStates.waiting_promo, F.data == 'skip_promo')
async def skip_promo(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await state.update_data(promo_code='')
    await _show_price_summary(call.message, state)


async def _show_price_summary(message, state: FSMContext) -> None:
    data = await state.get_data()

    tg_id = message.chat.id

    pricing = await api.calculate_price(
        telegram_id=tg_id,
        house_id=data['house_id'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        service_ids=data.get('service_ids', []),
        promo_code=data.get('promo_code', ''),
    )

    if not pricing or 'error' in pricing:
        err = pricing.get('error', 'Ошибка расчёта') if pricing else 'Ошибка'
        await message.answer(f'❌ {err}')
        return

    start_display = data['start_date'].replace('-', '.')[8:] + '.' + data['start_date'][5:7] + '.' + data['start_date'][:4]

    text = (
        f'📋 <b>Итог бронирования</b>\n\n'
        f'📅 {data["start_date"]} — {data["end_date"]} ({pricing["days"]} дн.)\n'
        f'🏠 Аренда: {pricing["base_price"]} ₽\n'
    )
    if float(pricing.get('services_cost', 0)) > 0:
        text += f'🛠 Услуги: {pricing["services_cost"]} ₽\n'
    if float(pricing.get('discount_amount', 0)) > 0:
        text += f'🎁 Скидка ({pricing["discount_pct"]}%): −{pricing["discount_amount"]} ₽\n'
    text += (
        f'\n💰 <b>Итого: {pricing["total_price"]} ₽</b>\n'
        f'💳 Предоплата (10%): <b>{pricing["prepayment_amount"]} ₽</b>\n'
        f'💳 Остаток при заезде: {pricing["remaining_amount"]} ₽'
    )

    await state.update_data(pricing=pricing)
    await state.set_state(BookingStates.confirming)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✅ Подтвердить и забронировать', callback_data='confirm_create_booking'),
        InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_booking_flow'),
    )
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode='HTML')


@router.callback_query(BookingStates.confirming, F.data == 'confirm_create_booking')
async def confirm_create_booking(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer('Создаём бронирование...')
    data = await state.get_data()
    tg_id = call.from_user.id

    booking = await api.create_booking(
        telegram_id=tg_id,
        house_id=data['house_id'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        service_ids=data.get('service_ids', []),
        promo_code=data.get('promo_code', ''),
    )

    await state.clear()

    if not booking or 'error' in booking:
        err = booking.get('error', 'Ошибка создания') if booking else 'Ошибка'
        await call.message.answer(f'❌ {err}')
        return

    await call.message.answer(
f'✅      <b>Бронирование создано!</b>\n\n'
        f'📅 {booking["start_date"]} — {booking["end_date"]}\n'
        f'💰 К оплате (10%): <b>{booking["prepayment_amount"]} ₽</b>',
        reply_markup=confirm_booking_keyboard(booking['id']),
        parse_mode='HTML'
    )


@router.callback_query(BookingStates.confirming, F.data == 'cancel_booking_flow')
async def cancel_booking_flow(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer('Отменено')
    await call.message.answer('Бронирование отменено.', reply_markup=main_menu_keyboard())
