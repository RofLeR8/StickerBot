import os
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import check_access, add_operation
from database.models import SOperAdd
from keyboards.reply import register_kb

logger = logging.getLogger(__name__)
router = Router()

STICKER_SET_NAME = os.getenv("STICKER_SET_NAME")


class Form(StatesGroup):
    delete_sticker = State()
    delete_sticker_confirm = State()


@router.message(F.text == "➖Sticker")
async def handle_delete(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id
    logger.info("User %d: delete sticker request", user_id)
    
    if not await check_access(session, user_id):
        logger.warning("User %d: denied access - not registered", user_id)
        await message.answer(
            "Вам не разрешено пользоваться ботом. \n"
            "Использование бота разрешено семейству Кабалиных.\n"
            "Отправьте заявку на регистрацию.\n"
            "Если произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None,
            reply_markup=register_kb(),
        )
        return
    
    await state.set_state(Form.delete_sticker)
    logger.info("User %d: waiting for sticker", user_id)
    await message.answer("Отправьте стикер, который хотите удалить.")


@router.message(Form.delete_sticker)
async def delete_sticker(message: Message, bot: Bot, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    logger.info("User %d: sent sticker for deletion", user_id)
    
    sticker = message.sticker
    if not sticker:
        logger.warning("User %d: message is not a sticker", user_id)
        await message.answer("❌ Это не стикер! Попробуйте снова.", parse_mode=None)
        await state.clear()
        return

    sticker_set_name = sticker.set_name
    sticker_id = sticker.file_id
    logger.info("User %d: sticker file_id=%s, set_name=%s", user_id, sticker_id, sticker_set_name)

    if sticker_set_name != STICKER_SET_NAME:
        logger.warning("User %d: sticker from wrong set %s (expected %s)", 
                       user_id, sticker_set_name, STICKER_SET_NAME)
        await message.answer(
            f"❌ Этот стикер не из вашего набора!\n"
            f"Ваш набор: {STICKER_SET_NAME}\n"
            f"Стикер из: {sticker_set_name}",
            parse_mode=None,
        )
        await state.clear()
        return

    await state.update_data(pending_delete_sticker_id=sticker_id)
    await state.set_state(Form.delete_sticker_confirm)
    logger.info("User %d: waiting for confirmation to delete sticker %s", user_id, sticker_id)
    await message.answer(
        "Удалить этот стикер из набора?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да", callback_data="delete_sticker_yes"),
                    InlineKeyboardButton(text="❌ Нет", callback_data="delete_sticker_no"),
                ]
            ]
        ),
    )


@router.callback_query(Form.delete_sticker_confirm, F.data == "delete_sticker_yes")
async def delete_sticker_confirm_yes(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
):
    user_id = callback.from_user.id
    logger.info("User %d: confirmed sticker deletion", user_id)
    
    await callback.answer()
    data = await state.get_data()
    sticker_id = data.get("pending_delete_sticker_id")
    
    if not sticker_id:
        logger.error("User %d: sticker ID not found in state (session expired)", user_id)
        await callback.message.edit_text(
            "❌ Сессия истекла. Выберите стикер заново (➖Sticker)."
        )
        await state.clear()
        return

    try:
        logger.info("User %d: deleting sticker %s", user_id, sticker_id)
        result = await bot.delete_sticker_from_set(sticker=sticker_id)
    except Exception as e:
        logger.exception("User %d: error deleting sticker: %s", user_id, str(e))
        await callback.message.edit_text(f"❌ Не удалось удалить стикер: {e}")
        await state.clear()
        return

    if result:
        logger.info("User %d: sticker %s deleted successfully", user_id, sticker_id)
        await add_operation(
            session,
            SOperAdd(user_id=user_id, type_op="delete", sticker_id=sticker_id),
        )
        await callback.message.edit_text("✅ Стикер удалён из набора.")
        await callback.message.answer(
            "Ссылка на стикерпак\n"
            "https://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot\n\n"
            "Удачи :)"
        )
    await state.clear()


@router.callback_query(Form.delete_sticker_confirm, F.data == "delete_sticker_no")
async def delete_sticker_confirm_no(callback: CallbackQuery, state: FSMContext):
    logger.info("User %d: cancelled sticker deletion", callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text("❌Удаление отменено.")
    await state.clear()
