from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    waiting_start_date = State()
    waiting_end_date = State()
    selecting_services = State()
    waiting_promo = State()
    confirming = State()


class SupportStates(StatesGroup):
    waiting_message = State()
