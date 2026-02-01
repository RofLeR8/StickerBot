import os
import tempfile
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from aiogram import Bot, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    check_access,
    check_admin,
    get_user_by_id,
    add_user as crud_add_user,
    add_operation,
)
from database.models import SUserAdd, SOperAdd
from keyboards.reply import common_kb, admin_kb
from keyboards.inline import support_keyboard
from image.utils import resize_image, remove_background

load_dotenv("./src/.env")


router = Router()


class Form(StatesGroup):
    choose = State()
    choose_emoji = State()
    delete = State()
    add_user = State()

# --- Start / Help ---

@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    if await check_access(session, user_id):
        is_admin = await check_admin(session, user_id)
        await message.answer(
            "Привет, вам разрешено пользоваться ботом. Бот управляет стикерпаком Кабалиных(https://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot)",
            parse_mode=None,
            reply_markup=common_kb(is_admin),
        )
    else:
        await message.answer(
            "Вам не разрешено пользоваться ботом. Использование бота разрешено семейству Кабалиных. Если произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None,
        )


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    if await check_access(session, user_id):
        await message.answer("Если возникли ошибки, баги или неисправности пишите:", reply_markup=support_keyboard())

