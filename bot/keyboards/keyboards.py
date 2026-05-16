from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text='🏠 Найти дом'),
        KeyboardButton(text='📖 Мои брони'),
    )
    builder.row(KeyboardButton(text='🔗 Моя реферальная ссылка'))
    builder.row(KeyboardButton(text='ℹ️ Поддержка'))

    return builder.as_markup(resize_keyboard=True)


def houses_navigation_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text='◀️', callback_data=f'houses_page:{page-1}'))
    nav.append(InlineKeyboardButton(text=f'{page}/{total_pages}', callback_data='noop'))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text='▶️', callback_data=f'houses_page:{page+1}'))
    if nav:
        builder.row(*nav)
    return builder.as_markup()


def house_card_keyboard(house_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='📅 Забронировать',
        callback_data=f'book_house:{house_id}'
    ))
    builder.row(InlineKeyboardButton(
        text='◀️ К списку',
        callback_data='houses_page:1'
    ))
    return builder.as_markup()


def services_keyboard(services: list, selected_ids: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        is_selected = svc['id'] in selected_ids
        mark = '✅' if is_selected else '⬜'
        price_note = f'×дни' if svc['is_daily'] else ''
        builder.row(InlineKeyboardButton(
            text=f'{mark} {svc["name"]} — {svc["price"]}₽{price_note}',
            callback_data=f'toggle_service:{svc["id"]}'
        ))
    builder.row(
        InlineKeyboardButton(text='✅ Продолжить', callback_data='services_done'),
        InlineKeyboardButton(text='❌ Без услуг', callback_data='services_skip'),
    )
    return builder.as_markup()


def confirm_booking_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text='💳 Оплатить предоплату (10%)',
            callback_data=f'pay_prepayment:{booking_id}'
        )
    )
    builder.row(
        InlineKeyboardButton(
            text='❌ Отменить',
            callback_data=f'cancel_booking:{booking_id}'
        )
    )
    return builder.as_markup()


def booking_actions_keyboard(booking: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    b_id = booking['id']
    status = booking['status']
    is_checked_in = booking.get('is_checked_in', False)

    if status == 'pending':
        builder.row(InlineKeyboardButton(
            text='💳 Оплатить предоплату',
            callback_data=f'pay_prepayment:{b_id}'
        ))
        builder.row(InlineKeyboardButton(
            text='❌ Отменить',
            callback_data=f'cancel_booking:{b_id}'
        ))
    elif status == 'partially_paid' and is_checked_in:
        builder.row(InlineKeyboardButton(
            text='💳 Оплатить остаток',
            callback_data=f'pay_remaining:{b_id}'
        ))
    elif status == 'partially_paid':
        builder.row(InlineKeyboardButton(
            text='📍 Я на месте',
            callback_data=f'checkin:{b_id}'
        ))
        builder.row(InlineKeyboardButton(
            text='❌ Отменить',
            callback_data=f'cancel_booking:{b_id}'
        ))

    return builder.as_markup()


def checkin_pay_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text='💳 Оплатить остаток',
        callback_data=f'pay_remaining:{booking_id}'
    ))
    return builder.as_markup()


def promo_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='🎟 Ввести промокод', callback_data='enter_promo'),
        InlineKeyboardButton(text='➡️ Без промокода', callback_data='skip_promo'),
    )
    return builder.as_markup()


def referral_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='🔗 Моя реферальная ссылка',
        switch_inline_query=referral_link
    ))
    return builder.as_markup()


def cancel_confirm_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✅ Да, отменить', callback_data=f'confirm_cancel:{booking_id}'),
        InlineKeyboardButton(text='◀️ Назад', callback_data=f'view_booking:{booking_id}'),
    )
    return builder.as_markup()
