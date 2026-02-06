from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def common_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="➕Sticker"), KeyboardButton(text="➖Sticker")]
    ]
    if is_admin:
        kb_list.append(
            [KeyboardButton(text="⚙️Admin Panel")]
        )
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
    return keyboard


def admin_kb() -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="➕ Добавить пользователя")],
        [KeyboardButton(text="👥 Управление пользователями")],
        [KeyboardButton(text="📝 Список заявок")],
        [KeyboardButton(text="⬅️ В главное меню")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
    return keyboard

def register_kb():
    kb_list = [
        [KeyboardButton(text="📝 Зарегистрироваться")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
    return keyboard