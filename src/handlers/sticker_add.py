import os
import tempfile
import datetime
import emoji
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile, InputSticker
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import check_access, check_admin, add_operation
from database.models import SOperAdd
from keyboards.reply import common_kb, register_kb
from keyboards.inline import choose_option_bg, skip_keywords_kb
from image.utils import resize_image, remove_background

router = Router()

PHOTO_DIR = os.getenv("PHOTO_DIR")
STICKER_SET_NAME = os.getenv("STICKER_SET_NAME")


class Form(StatesGroup):
    choose_image = State()
    choose_option = State()
    choose_emoji = State()
    choose_keywords = State()


def is_valid_sticker_emoji(text: str) -> bool:
    """
    Проверяет, что строка содержит хотя бы один эмодзи и не содержит букв/цифр.
    """
    text = text.strip()
    if not text:
        return False
    without_emojis = emoji.replace_emoji(text, replace='')
    return without_emojis.strip() == ""


@router.message(F.text == "➕Sticker")
async def add_sticker(message: Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    if not user_id:
        return
    if not await check_access(session, user_id):
        await message.answer(
            "Вам не разрешено пользоваться ботом. \n"
            "Использование бота разрешено семейству Кабалиных.\n"
            "Отправьте заявку на регистрацию. \n"
            "Если произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None,
            reply_markup=register_kb(),
        )
        return

    await state.set_state(Form.choose_image)
    await message.answer(
        "Отправьте фото для создания стикера или готовый стикер из любого набора — "
        "он будет добавлен в ваш стикерпак."
    )


@router.message(F.photo, Form.choose_image)
async def handle_photo(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    if not user_id:
        return
    if not await check_access(session, user_id):
        await message.answer(
            "Вам не разрешено пользоваться ботом. \n"
            "Использование бота разрешено семейству Кабалиных.\n"
            "Отправьте заявку на регистрацию.\n"
            "Если произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None,
            reply_markup=register_kb(),
        )
        return

    photo = message.photo[-1]
    temp_input_path = os.path.join(
        tempfile.gettempdir(),
        f"{user_id}_{int(datetime.datetime.now().timestamp())}.jpg"
    )

    await bot.download(photo, destination=temp_input_path)
    await state.update_data(temp_photo_path=temp_input_path)
    await message.answer("Хочешь удалить фон?", reply_markup=choose_option_bg())
    await state.set_state(Form.choose_option)


@router.message(F.sticker, Form.choose_image)
async def handle_sticker(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    if not user_id:
        return
    if not await check_access(session, user_id):
        await message.answer(
            "Вам не разрешено пользоваться ботом. Использование бота разрешено семейству Кабалиных. "
            "Отправьте заявку на регистрацию. Если произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None,
            reply_markup=register_kb(),
        )
        return

    sticker = message.sticker
    if sticker.is_animated or sticker.is_video:
        await message.answer(
            "❌ Поддерживаются только статичные стикеры. "
            "Анимированные и видео-стикеры нельзя конвертировать в PNG."
        )
        return

    try:
        file = await bot.get_file(sticker.file_id)
        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"{user_id}_{int(datetime.datetime.now().timestamp())}.webp"
        )
        await bot.download(file, destination=temp_path)

        time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        final_path = os.path.join(PHOTO_DIR, f"{user_id}_{time_str}.png")
        resize_image(temp_path, final_path)
        try:
            os.unlink(temp_path)
        except OSError:
            pass

        await state.update_data(sticker_path=final_path)
        await state.set_state(Form.choose_emoji)
        await message.answer(
            "✅ Стикер конвертирован в PNG.\n\n"
            "Теперь отправьте эмодзи для стикера (например: 😊 или 🔥🎉)"
        )
    except Exception as e:
        await state.clear()
        await message.answer(f"❌ Ошибка при обработке стикера:\n{str(e)}")


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
    time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    final_path = os.path.join(PHOTO_DIR, f"{user_id}_{time_str}.png")

    try:
        resize_image(temp_input_path, final_path)
        if callback.data == "remove_bg":
            remove_background(final_path)
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка обработки: {str(e)}")
    finally:
        try:
            os.unlink(temp_input_path)
        except OSError:
            pass

    await state.update_data(sticker_path=final_path)
    await state.set_state(Form.choose_emoji)
    await callback.message.edit_text(
        "✅Изображение готово.\n\n"
        "Теперь отправьте эмодзи для стикера (например: 😊 или 🔥🎉)"
    )


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
    await message.answer(
        "Отлично! Теперь отправьте ключевые слова через запятую "
        "или нажмите кнопку ниже, чтобы пропустить.",
        reply_markup=skip_keywords_kb(),
    )
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


async def finish_sticker_creation(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
    user_id: int,
):
    data = await state.get_data()
    sticker_path = data.get("sticker_path")
    is_admin = await check_admin(session, user_id)
    sticker_emoji = data.get("sticker_emoji", "❓")
    keywords = data.get("sticker_keywords", "")

    if not sticker_path or not os.path.exists(sticker_path):
        await message.answer("❌ Ошибка: стикер утерян.")
        await state.clear()
        return

    sticker_set_name = STICKER_SET_NAME

    try:
        sticker_file = FSInputFile(sticker_path)
        input_sticker = InputSticker(
            sticker=sticker_file,
            emoji_list=[sticker_emoji],
            format="static",
            keywords=keywords or None,
        )

        result = await bot.add_sticker_to_set(
            user_id=user_id,
            name=sticker_set_name,
            sticker=input_sticker,
        )

        if result:
            await message.answer(
                "✅ Стикер успешно добавлен в пак!",
                reply_markup=common_kb(is_admin),
            )

            sticker_set = await bot.get_sticker_set(name=STICKER_SET_NAME)
            file_id = sticker_set.stickers[-1].file_id
            oper = SOperAdd(
                user_id=user_id,
                type_op="add",
                sticker_id=file_id,
            )
            await add_operation(session, oper)
            await bot.send_sticker(chat_id=message.chat.id, sticker=file_id)
            await bot.send_message(
                chat_id=message.chat.id,
                text=(
                    "Ссылка на стикерпак\n"
                    "https://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot\n\n"
                    "Удачи :)"
                ),
            )
        else:
            await message.answer("❌ Не удалось добавить стикер. Возможно, лимит пака исчерпан.")

    except Exception as e:
        error_msg = str(e)
        await message.answer(
            f"❌ Ошибка при добавлении стикера:\n{error_msg}",
            reply_markup=common_kb(is_admin),
        )
        try:
            sticker_set = await bot.get_sticker_set(name=STICKER_SET_NAME)
            file_id = sticker_set.stickers[-1].file_id
        except Exception:
            file_id = ""
        oper = SOperAdd(
            user_id=user_id,
            type_op="add_sticker_error",
            sticker_id=file_id,
        )
        await add_operation(session, oper)

    finally:
        await state.clear()
