from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def support_keyboard():
    kb_list = [
        [InlineKeyboardButton(text="Общий чат Кабалиных", url="https://t.me/+ry3wBlM3qQQ2YzE6")],
        [InlineKeyboardButton(text="Лично админу бота",url="https://t.me/Vot_eto_rofl")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def choose_option_bg():
    kb_list = [
        [InlineKeyboardButton(text="✅ Удалить фон", callback_data="remove_bg")],
        [InlineKeyboardButton(text="❌ Оставить как есть", callback_data="keep_bg")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def skip_keywords_kb():
    kb_list = [
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_keywords")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard
