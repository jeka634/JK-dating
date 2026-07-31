from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    language = State()
    rules = State()
    name = State()
    age = State()
    gender = State()
    looking_for = State()
    city = State()
    description = State()
    photos = State()


class ComplaintStates(StatesGroup):
    reason = State()


class EditProfileStates(StatesGroup):
    name = State()
    age = State()
    city = State()
    description = State()
    photos = State()


class FilterStates(StatesGroup):
    age_min = State()
    age_max = State()
    city = State()


class TonConnectStates(StatesGroup):
    waiting_wallet = State()
