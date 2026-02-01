from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def support_keyboard():
    kb_list = [
        [InlineKeyboardButton(text="Общий чат Кабалиных", url="https://t.me/+ry3wBlM3qQQ2YzE6")],
        [InlineKeyboardButton(text="Лично админу бота",url="https://t.me/Vot_eto_rofl")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard