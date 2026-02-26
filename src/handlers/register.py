from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database.crud import (
    get_user_by_id,
    get_all_admins,
    delete_user_by_id,
    set_user_approved,
)
from database.schemas import UserModel

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "📝 Зарегистрироваться")
async def register_request(message: Message, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    logger.info("User %d: registration request", user_id)
    
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name if message.from_user.last_name else None
    username = (message.from_user.username or "—").strip()

    existing = await get_user_by_id(session, user_id)
    if existing:
        if existing.is_approved:
            logger.info("User %d: already registered and approved", user_id)
            await message.answer("Вы уже зарегистрированы!")
        else:
            logger.info("User %d: already registered but pending approval", user_id)
            await message.answer(
                "Ваша заявка уже отправлена и ожидает подтверждения."
            )
        return

    new_user = UserModel(
        id=user_id,
        first_name=first_name,
        last_name=last_name,
        is_admin=False,
        is_approved=False,
    )
    await session.add(new_user)
    await session.commit()
    logger.info("User %d: registration saved to database, pending approval", user_id)

    admins = await get_all_admins(session)
    logger.info("User %d: notifying %d admins", user_id, len(admins))
    
    for admin in admins:
        try:
            await bot.send_message(
                chat_id=admin.id,
                text=(
                    f"🔔 Новая заявка на регистрацию:\n"
                    f"ID: {user_id}\n"
                    f"Username: @{username}\n"
                    f"Имя: {first_name or '—'} {last_name or '—'}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="✅ Одобрить", callback_data=f"approve_user_{user_id}"
                            ),
                            InlineKeyboardButton(
                                text="❌ Отклонить", callback_data=f"reject_user_{user_id}"
                            ),
                        ]
                    ]
                ),
            )
        except Exception as e:
            logger.error("Failed to notify admin %d: %s", admin.id, str(e))

    await message.answer(
        "✅ Заявка отправлена! Ожидайте подтверждения от администратора."
    )


@router.callback_query(F.data.startswith("approve_user_"))
async def approve_user(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split("_")[-1])
    user = await get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    if user.is_approved:
        await callback.answer("Пользователь уже одобрен", show_alert=True)
        return

    await set_user_approved(session, user_id, approved=True)
    try:
        await callback.bot.send_message(
            user_id,
            "✅ Ваша заявка одобрена! Теперь вы можете пользоваться ботом.",
        )
    except Exception:
        pass
    await callback.message.edit_text("✅ Пользователь одобрен")
    await callback.answer()


@router.callback_query(F.data.startswith("reject_user_"))
async def reject_user(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split("_")[-1])
    try:
        await delete_user_by_id(session, user_id)
    except ValueError:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    try:
        await callback.bot.send_message(user_id, "❌ Ваша заявка отклонена.")
    except Exception:
        pass
    await callback.message.edit_text("❌ Пользователь отклонён")
    await callback.answer()
