from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    check_admin,
    check_access,
    get_user_by_id,
    add_user as crud_add_user,
    get_all_users,
    delete_user_by_id,
    set_user_approved,
    set_user_admin,
    get_pending_users,
    get_operations_paginated,
    get_operations_count,
)
from database.models import SUserAdd
from database.schemas import UserModel
from keyboards.reply import admin_kb, common_kb
from keyboards.inline import (
    user_action_kb,
    user_permissions_kb,
    user_delete_confirm_kb,
    operations_pagination_kb,
)

router = Router()


class Form(StatesGroup):
    add_user = State()
    get_sticker_file_id = State()


@router.message(F.text == "⚙️Admin Panel")
async def handle_admin_panel(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    if not await check_admin(session, user_id):
        await message.answer("❌ Вы не админ бота!")
        return
    await message.answer("Админ-панель. Выберите действие:", reply_markup=admin_kb())


@router.message(F.text == "⬅️ В главное меню")
async def admin_back_to_main(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    is_admin = await check_admin(session, user_id) if await check_access(session, user_id) else False
    await message.answer(
        f"Привет {message.from_user.first_name}, вам разрешено пользоваться ботом.\n"
        "Бот управляет стикерпаком Кабалиных\n"
        "https://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot",
        parse_mode=None,
        reply_markup=common_kb(is_admin),
    )


@router.message(F.text == "➕ Добавить пользователя")
async def admin_add_user_start(message: Message, session: AsyncSession, state: FSMContext):
    if not await check_admin(session, message.from_user.id):
        return
    await state.set_state(Form.add_user)
    await message.answer(
        "Отправьте Telegram ID пользователя(обяз.), имя(необяз.), фамилию(необяз.) "
        "через запятую, в указаном порядке пользователя.\n"
        "Чтобы отменить — нажмите «⬅️ В главное меню»."
    )


@router.message(Form.add_user, F.text)
async def admin_add_user_by_text(message: Message, session: AsyncSession, state: FSMContext):
    if not await check_admin(session, message.from_user.id):
        return
    text = [t.strip() for t in message.text.split(",")]
    user_id = text[0] if text[0] else None
    if not user_id:
        await message.answer("❌Неправильный формат ввода. Попробуйте снова.")
        await state.clear()
        return
    first_name = text[1] if len(text) >= 2 else None
    last_name = text[2] if len(text) == 3 else None

    if await get_user_by_id(session, user_id):
        await message.answer("Этот пользователь уже есть в базе.")
        await state.clear()
        return

    try:
        await crud_add_user(
            session,
            SUserAdd(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                is_admin=False,
                is_approved=True,
            ),
        )
        await message.answer("✅ Пользователь добавлен и сразу одобрен (доступ открыт).")
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении: {e}")
    await state.clear()


@router.message(Form.add_user)
async def admin_add_user_other(message: Message, session: AsyncSession, state: FSMContext):
    if not await check_admin(session, message.from_user.id):
        return
    if message.forward_from:
        target_id = message.forward_from.id
        first_name = message.forward_from.first_name
        last_name = message.forward_from.last_name or None

        if await get_user_by_id(session, target_id):
            await message.answer("Этот пользователь уже есть в базе.")
            await state.clear()
            return

        try:
            await crud_add_user(
                session,
                SUserAdd(
                    id=target_id,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=False,
                    is_approved=True,
                ),
            )
            await message.answer("✅ Пользователь добавлен и сразу одобрен (доступ открыт).")
        except Exception as e:
            await message.answer(f"❌ Ошибка при добавлении: {e}")
        await state.clear()
        return

    await message.answer(
        "Отправьте Telegram ID (число) или перешлите сообщение от пользователя."
    )


@router.message(F.text == "👥 Управление пользователями")
async def admin_manage_users(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return
    users = await get_all_users(session)
    if not users:
        await message.answer("В базе нет пользователей.")
        return

    chunk = users[:15]
    for u in chunk:
        name = f"{u.first_name or ''} {u.last_name or ''}".strip() or f"ID {u.id}"
        status = "👑" if u.is_admin else ""
        status += " ✅" if u.is_approved else " ⏳"
        await message.answer(
            f"👤 {name} (ID: {u.id}) {status}",
            reply_markup=user_action_kb(u.id),
        )
    if len(users) > 15:
        await message.answer(f"... и ещё {len(users) - 15} пользователей.")


@router.callback_query(F.data.startswith("admin_perm_"))
async def admin_user_permissions(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int(callback.data.split("_")[-1])
    user = await get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"ID {user.id}"
    text = (
        f"🔐 Права: {name} (ID: {user.id})\n"
        f"Одобрен: {'да' if user.is_approved else 'нет'}\n"
        f"Админ: {'да' if user.is_admin else 'нет'}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=user_permissions_kb(user.id, user.is_approved, user.is_admin),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("perm_approve_"))
async def admin_toggle_approve(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    parts = callback.data.split("_")
    user_id = int(parts[2])
    approved = bool(int(parts[3]))
    user = await get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await set_user_approved(session, user_id, approved=approved)
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"ID {user.id}"
    try:
        await callback.bot.send_message(
            user_id,
            "✅ Ваш доступ к боту одобрен!" if approved else "❌ Ваш доступ к боту заблокирован.",
        )
    except Exception:
        pass
    await callback.message.edit_text(
        f"🔐 {name}: {'одобрен' if approved else 'заблокирован'}",
        reply_markup=user_permissions_kb(user_id, approved, user.is_admin),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("perm_admin_"))
async def admin_toggle_admin(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    parts = callback.data.split("_")
    user_id = int(parts[2])
    is_admin = bool(int(parts[3]))
    user = await get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await set_user_admin(session, user_id, is_admin=is_admin)
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"ID {user.id}"
    try:
        await callback.bot.send_message(
            user_id,
            "👑 Вам выданы права администратора бота." if is_admin else "👤 Права администратора сняты.",
        )
    except Exception:
        pass
    await callback.message.edit_text(
        f"🔐 {name}: {'админ' if is_admin else 'обычный пользователь'}",
        reply_markup=user_permissions_kb(user_id, user.is_approved, is_admin),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users_back")
async def admin_users_back(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer()
        return
    await callback.message.edit_text(
        "⬅️ Возврат. Используйте «👥 Управление пользователями» для нового списка."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_"))
async def admin_delete_user(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback.data == "admin_del_cancel":
        await callback.message.edit_text("❌ Удаление отменено.")
        await callback.answer()
        return

    if callback.data.startswith("admin_del_confirm_"):
        user_id = int(callback.data.split("_")[-1])
        user = await get_user_by_id(session, user_id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return
        try:
            await delete_user_by_id(session, user_id)
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"ID {user.id}"
            try:
                await callback.bot.send_message(
                    user_id, "❌ Вы удалены из базы пользователей бота."
                )
            except Exception:
                pass
            await callback.message.edit_text(f"✅ Пользователь {name} удалён.")
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
        await callback.answer()
        return

    user_id = int(callback.data.split("_")[-1])
    user = await get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"ID {user.id}"
    await callback.message.edit_text(
        f"🗑 Удалить пользователя {name} (ID: {user_id})?",
        reply_markup=user_delete_confirm_kb(user_id),
    )
    await callback.answer()


@router.message(F.text == "📝 Список заявок")
async def admin_list_requests(message: Message, session: AsyncSession, bot: Bot):
    if not await check_admin(session, message.from_user.id):
        return
    pending = await get_pending_users(session)
    if not pending:
        await message.answer("Заявок на регистрацию нет.")
        return
    for u in pending:
        name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "—"
        text = f"🔔 Заявка: ID {u.id}, {name}"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Одобрить", callback_data=f"approve_user_{u.id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить", callback_data=f"reject_user_{u.id}"
                    ),
                ]
            ]
        )
        await message.answer(text, reply_markup=kb)


@router.message(F.text == "📋 История операций")
async def admin_list_operations(message: Message, session: AsyncSession, state: FSMContext):
    """Показать последние операции с пагинацией."""
    if not await check_admin(session, message.from_user.id):
        return
    await show_operations_page(message, session, state, page=1)


async def show_operations_page(message: Message, session: AsyncSession, state: FSMContext, page: int):
    """Показать страницу операций."""
    limit = 5
    offset = (page - 1) * limit

    operations = await get_operations_paginated(session, limit=limit, offset=offset)
    total_count = await get_operations_count(session)
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    if not operations:
        await message.answer("📋 История операций пуста.")
        return

    lines = []
    for i, op in enumerate(operations, start=offset + 1):
        user = await get_user_by_id(session, op.user_id)
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() if user else f"ID {op.user_id}"
        op_type_map = {
            "add": "➕ Добавление",
            "delete": "➖ Удаление",
            "add_sticker_error": "❌ Ошибка добавления",
        }
        op_type = op_type_map.get(op.type_op, op.type_op)
        created = op.created_at.strftime("%d.%m.%Y %H:%M") if op.created_at else "—"

        lines.append(
            f"{i}. {op_type} | {user_name} | {created}\n"
            f"   Стикер: <code>{op.sticker_id}</code>"
        )

    text = "📋 История операций:\n\n" + "\n\n".join(lines)
    text += f"\n\n📊 Страница {page}/{total_pages}"

    kb = operations_pagination_kb(page, total_pages)

    # Проверяем, есть ли уже отправленное сообщение в state
    data = await state.get_data()
    msg_id = data.get("ops_message_id")

    if msg_id:
        # Редактируем существующее сообщение
        try:
            await message.bot.edit_message_text(
                text=text,
                chat_id=message.chat.id,
                message_id=msg_id,
                reply_markup=kb,
                parse_mode="HTML",
            )
        except Exception:
            # Если редактирование не удалось, отправляем новое
            new_msg = await message.answer(text, reply_markup=kb, parse_mode="HTML")
            await state.update_data(ops_message_id=new_msg.message_id)
    else:
        # Отправляем новое сообщение
        new_msg = await message.answer(text, reply_markup=kb, parse_mode="HTML")
        await state.update_data(ops_message_id=new_msg.message_id)


@router.message(F.text == "🔍 Найти стикер")
async def admin_get_sticker_by_file_id(message: Message, session: AsyncSession, state: FSMContext):
    """Запрос file_id для просмотра стикера."""
    if not await check_admin(session, message.from_user.id):
        return
    await message.answer(
        "🔍 Отправьте file_id стикера для просмотра.\n"
        "Можно скопировать из истории операций.\n"
        "Для отмены нажмите /cancel"
    )
    await state.set_state(Form.get_sticker_file_id)


@router.message(Form.get_sticker_file_id)
async def admin_send_sticker_by_file_id(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Отправить стикер по полученному file_id."""
    if not await check_admin(session, message.from_user.id):
        return

    file_id = message.text.strip()

    if not file_id:
        await message.answer("❌ Пустой file_id. Отправьте file_id или нажмите /cancel")
        return

    try:
        await bot.send_sticker(chat_id=message.chat.id, sticker=file_id)
        await message.answer("✅ Стикер найден!", reply_markup=admin_kb())
    except Exception as e:
        error_msg = str(e).lower()
        if 'sticker_document_invalid' in error_msg or 'file_id_invalid' in error_msg:
            await message.answer(
                f"❌ Стикер не найден или удалён Telegram\n"
                f"<code>{file_id}</code>\n\n"
                "Попробуйте другой file_id или нажмите /cancel",
                parse_mode="HTML",
                reply_markup=admin_kb(),
            )
        else:
            await message.answer(
                f"❌ Ошибка: {error_msg}\n"
                f"<code>{file_id}</code>\n\n"
                "Попробуйте другой file_id или нажмите /cancel",
                parse_mode="HTML",
                reply_markup=admin_kb(),
            )

    await state.clear()


@router.callback_query(F.data.startswith("ops_page_"))
async def callback_operations_page(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Переключение страницы операций."""
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    page = int(callback.data.split("_")[-1])
    await show_operations_page(callback.message, session, state, page=page)
    await callback.answer()


@router.callback_query(F.data == "ops_refresh")
async def callback_operations_refresh(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Обновить список операций."""
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await show_operations_page(callback.message, session, state, page=1)
    await callback.answer()
