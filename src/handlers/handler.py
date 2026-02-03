import os
import tempfile
import asyncio
import aiofiles
import datetime
import emoji
from pathlib import Path

from dotenv import load_dotenv
from aiogram import Bot, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, FSInputFile, CallbackQuery, InputSticker
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
from keyboards.inline import support_keyboard, choose_option_bg, skip_keywords_kb
from image.utils import resize_image, remove_background


load_dotenv("./src/.env")


router = Router()
PHOTO_DIR = os.getenv("PHOTO_DIR")
STICKER_SET_NAME = os.getenv("STICKER_SET_NAME")
os.makedirs(PHOTO_DIR, exist_ok=True)

class Form(StatesGroup):
    choose_image = State()
    choose_option = State()
    choose_emoji = State()
    choose_keywords = State()
    delete = State()
    add_user = State()
    temp_photo_path = State()
    sticker_emoji = State()
    sticker_keywords= State()

# --- Start / Help ---

def is_valid_sticker_emoji(text: str) -> bool:
    """
    Проверяет, что строка содержит хотя бы один эмодзи и не содержит букв/цифр.
    """
    text = text.strip()
    if not text:
        return False

    # Убираем всё, что является эмодзи
    without_emojis = emoji.replace_emoji(text, replace='')

    # Если после удаления эмодзи остались только пробелы — OK
    return without_emojis.strip() == ""

@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    if await check_access(session, user_id):
        is_admin = await check_admin(session, user_id)
        await message.answer(
            "Привет, вам разрешено пользоваться ботом.\n Бот управляет стикерпаком Кабалиных\nhttps://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot",
            parse_mode=None,
            reply_markup=common_kb(is_admin),
        )
        await state.clear()
    else:
        await message.answer(
            "Вам не разрешено пользоваться ботом. \nИспользование бота разрешено семейству Кабалиных. \nЕсли произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None,
        )


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    if await check_access(session, user_id):
        await message.answer("Если возникли ошибки, баги или неисправности пишите:", reply_markup=support_keyboard())


@router.message(F.text == "➕Sticker")
async def add_sticker(message: Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    if not user_id: 
        return 
    if not await check_access(session, user_id):
        await message.answer(
            "Вам не разрешено пользоваться ботом. \nИспользование бота разрешено семейству Кабалиных. \nЕсли произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None,
        )
        return 
    
    await state.set_state(Form.choose_image)
    await message.answer("Отправьте мне изображение для стикера")


# --- Обработка фото ---
@router.message(F.photo, Form.choose_image)
async def handle_photo(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    if not user_id:
        return
    if not await check_access(session, user_id):  # ← await добавлен!
        await message.answer("Доступ запрещён.", parse_mode=None)
        return

    photo = message.photo[-1]

    # Генерируем временный путь
    temp_input_path = os.path.join(tempfile.gettempdir(), f"{user_id}_{int(datetime.datetime.utcnow().timestamp())}.jpg")

    # Скачиваем напрямую — проще и надёжнее
    await bot.download(photo, destination=temp_input_path) 

    # Сохраняем путь в FSM
    await state.update_data(temp_photo_path=temp_input_path)
    await message.answer("Хочешь удалить фон?", reply_markup=choose_option_bg())
    await state.set_state(Form.choose_option)


# --- Выбор обработки ---
@router.callback_query(Form.choose_option, F.data.in_({"remove_bg", "keep_bg"}))
async def process_choice(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    temp_input_path = data.get("temp_photo_path")

    if not temp_input_path or not os.path.exists(temp_input_path):
        await callback.message.edit_text("❌ Ошибка: файл утерян.")
        await state.clear()
        return

    user_id = callback.from_user.id
    time_str = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    final_path = os.path.join(PHOTO_DIR, f"{user_id}_{time_str}.png")

    try:
        resize_image(temp_input_path, final_path)
        if callback.data == "remove_bg":
            remove_background(final_path)        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка обработки: {str(e)}")
    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_input_path)
        except OSError:
            pass
    await state.update_data(sticker_path=final_path)
    await state.set_state(Form.choose_emoji)
    await callback.message.edit_text("✅Изображение готово.\n\nТеперь отправьте **эмодзи** для стикера (например: 😊 или 🔥🎉)")


@router.message(Form.choose_emoji)
async def handle_emoji(message: Message, state: FSMContext):
    text = message.text.strip()

    if not text:
        await message.answer("Пожалуйста, отправьте эмодзи.")
        return

    if not is_valid_sticker_emoji(text):
        await message.answer(
            "Некорректный ввод. Отправьте только эмодзи (например: 😊 или 🔥🎉).\n"
            "Буквы, цифры и символы не разрешены."
        )
        return

    if len(text) > 20:
        await message.answer("Слишком много эмодзи. Максимум — 20 символов.")
        return

    await state.update_data(sticker_emoji=text)
    await message.answer("Отлично! Теперь отправьте ключевые слова через запятую или нажмите кнопку ниже, чтобы пропустить.", reply_markup=skip_keywords_kb())
    await state.set_state(Form.choose_keywords)

@router.callback_query(Form.choose_keywords, F.data == "skip_keywords")
async def skip_keywords_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    await callback.answer()
    await state.update_data(sticker_keywords="")
    await callback.message.edit_text("Ключевые слова пропущены.")
    await finish_sticker_creation(callback.message, state, session, bot, callback.from_user.id)

@router.message(Form.choose_keywords)
async def handle_keywords(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    keywords = message.text.strip()
    
    words = [w.strip() for w in keywords.split(",") if w.strip()]
    if len(words) > 20:
        await message.answer("Слишком много ключевых слов. Максимум — 20.")
        return
    if any(len(w) > 64 for w in words):
        await message.answer("Каждое ключевое слово должно быть не длиннее 64 символов.")
        return

    clean_keywords = [i for i in words]
    await state.update_data(sticker_keywords=clean_keywords)
    await message.answer("Ключевые слова сохранены!")
    await finish_sticker_creation(message, state, session, bot, message.from_user.id)

async def finish_sticker_creation(message: Message, state: FSMContext, session: AsyncSession, bot: Bot, user_id: int):
    data = await state.get_data()
    sticker_path = data.get("sticker_path")
    emoji = data.get("sticker_emoji", "❓")
    keywords = data.get("sticker_keywords", "")

    if not sticker_path or not os.path.exists(sticker_path):
        await message.answer("❌ Ошибка: стикер утерян.")
        await state.clear()
        return

    sticker_set_name = STICKER_SET_NAME # ← замени на своё!

    try:
        # 1. Готовим файл
        sticker_file = FSInputFile(sticker_path)

        # 2. Создаём InputSticker
        input_sticker = InputSticker(
            sticker=sticker_file,
            emoji_list=[emoji],
            format="static", 
            keywords=keywords or None
        )

        # 3. Добавляем в стикерпак
        result = await bot.add_sticker_to_set(
            user_id=user_id,
            name=sticker_set_name,
            sticker=input_sticker
        )

        if result:
            await message.answer("✅ Стикер успешно добавлен в пак!", reply_markup=common_kb())
            
            sticker_set = await bot.get_sticker_set(name=STICKER_SET_NAME)
            file_id = sticker_set.stickers[-1].file_id
            oper = SOperAdd(
                user_id=user_id,
                type_op="add",
                sticker_id=file_id
            )
            await add_operation(session, oper)
            await bot.send_sticker(chat_id=message.chat.id, sticker=file_id)
            await bot.send_message(chat_id=message.chat.id, text="Ссылка на стикерпак\nhttps://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot\n\nУдачи :)")
        else:
            await message.answer("❌ Не удалось добавить стикер. Возможно, лимит пака исчерпан.")

    except Exception as e:
        error_msg = str(e)
        await message.answer(f"❌ Ошибка при добавлении стикера:\n{error_msg}", reply_markup=common_kb())
        
        sticker_set = await bot.get_sticker_set(name=STICKER_SET_NAME)
        file_id = sticker_set.stickers[-1].file_id
        oper = SOperAdd(
            user_id=user_id,
            operation_type="add_sticker_error",
            sticker_id=file_id
        )
        await add_operation(session, oper)

    finally:
        # Удаляем временный файл
        try:
            os.unlink(sticker_path)
        except OSError:
            pass
        await state.clear()