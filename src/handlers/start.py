import os
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import check_access, check_admin
from keyboards.reply import common_kb, register_kb
from keyboards.inline import support_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    logger.info("User %d: /start command", user_id)
    
    if await check_access(session, user_id):
        is_admin = await check_admin(session, user_id)
        logger.info("User %d: access granted, is_admin=%s", user_id, is_admin)
        await message.answer(
            f"Привет {message.from_user.first_name}, вам разрешено пользоваться ботом.\n"
            "Бот управляет стикерпаком Кабалиных\n"
            "https://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot",
            parse_mode=None,
            reply_markup=common_kb(is_admin),
        )
        await state.clear()
    else:
        logger.info("User %d: access denied - not registered", user_id)
        await message.answer(
            "Вам не разрешено пользоваться ботом. \n"
            "Использование бота разрешено семейству Кабалиных.\n"
            "Отправьте заявку на регистрацию.\n"
            "Если произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None,
            reply_markup=register_kb(),
        )


@router.message(Command("cancel"))
async def cancel_operation(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    for path_key in ("temp_photo_path", "sticker_path"):
        path = data.get(path_key)
        if path and isinstance(path, str) and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass
    await state.clear()

    user_id = message.from_user.id
    if await check_access(session, user_id):
        is_admin = await check_admin(session, user_id)
        await message.answer("Операция отменена.", reply_markup=common_kb(is_admin))
    else:
        await message.answer(
            "Операция отменена.\n"
            "Вам не разрешено пользоваться ботом. Использование бота разрешено семейству Кабалиных. "
            "Отправьте заявку на регистрацию или обращайтесь @Vot_eto_rofl",
            parse_mode=None,
            reply_markup=register_kb(),
        )


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    if await check_access(session, user_id):
        await message.answer(
            "Если возникли ошибки, баги или неисправности пишите:",
            reply_markup=support_keyboard(),
        )
