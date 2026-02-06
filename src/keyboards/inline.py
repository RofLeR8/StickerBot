from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# --- Админ: управление пользователями ---


def user_action_kb(user_id: int) -> InlineKeyboardMarkup:
    """Кнопки действий для пользователя: удалить, изменить права."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_del_{user_id}"),
            InlineKeyboardButton(text="🔐 Права", callback_data=f"admin_perm_{user_id}"),
        ]
    ])


def user_permissions_kb(user_id: int, is_approved: bool, is_admin: bool) -> InlineKeyboardMarkup:
    """Клавиатура изменения прав пользователя."""
    approved_btn = "✅ Одобрен" if is_approved else "❌ Заблокирован"
    admin_btn = "👑 Админ" if is_admin else "👤 Обычный"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=approved_btn,
                callback_data=f"perm_approve_{user_id}_{int(not is_approved)}"
            ),
        ],
        [
            InlineKeyboardButton(
                text=admin_btn,
                callback_data=f"perm_admin_{user_id}_{int(not is_admin)}"
            ),
        ],
        [InlineKeyboardButton(text="⬅️ К списку", callback_data="admin_users_back")],
    ])


def user_delete_confirm_kb(user_id: int) -> InlineKeyboardMarkup:
    """Подтверждение удаления пользователя."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"admin_del_confirm_{user_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_del_cancel"),
        ]
    ])


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
