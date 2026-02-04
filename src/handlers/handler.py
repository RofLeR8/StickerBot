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
from aiogram.types import Message, FSInputFile, CallbackQuery, InputSticker, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    check_access,
    check_admin,
    get_user_by_id,
    add_user as crud_add_user,
    add_operation,
    get_all_admins,
    get_pending_users,
    delete_user_by_id,
    set_user_approved,
)
from database.models import SUserAdd, SOperAdd
from database.schemas import UserModel
from keyboards.reply import common_kb, admin_kb, register_kb
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
    delete_sticker = State()
    delete_sticker_confirm = State()
    add_user = State()
    temp_photo_path = State()
    sticker_emoji = State()
    sticker_keywords= State()
    register = State()

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
            f"Привет {message.from_user.first_name}, вам разрешено пользоваться ботом.\n Бот управляет стикерпаком Кабалиных\nhttps://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot",
            parse_mode=None,
            reply_markup=common_kb(is_admin),
        )
        await state.clear()
    else:
        await message.answer(
            "Вам не разрешено пользоваться ботом. \nИспользование бота разрешено семейству Кабалиных.\nОтправьте заявку на регистрацию.\nЕсли произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None, reply_markup=register_kb()
        )


@router.message(Command("cancel"))
async def cancel_operation(message: Message, session: AsyncSession, state: FSMContext):
    # Удаляем фото из state, если пользователь отправил их в процессе создания стикера
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
            "Операция отменена.\nВам не разрешено пользоваться ботом. Использование бота разрешено семейству Кабалиных. Отправьте заявку на регистрацию или обращайтесь @Vot_eto_rofl",
            parse_mode=None,
            reply_markup=register_kb(),
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
            "Вам не разрешено пользоваться ботом. \nИспользование бота разрешено семейству Кабалиных.\nОтправьте заявку на регистрацию. \nЕсли произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None, reply_markup=register_kb()
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
        await message.answer(
            "Вам не разрешено пользоваться ботом. \nИспользование бота разрешено семейству Кабалиных.\nОтправьте заявку на регистрацию.\nЕсли произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None, reply_markup=register_kb()
        )
        return

    photo = message.photo[-1]

    # Генерируем временнй путь
    temp_input_path = os.path.join(tempfile.gettempdir(), f"{user_id}_{int(datetime.datetime.now(datetime.UTC).timestamp())}.jpg")

    await bot.download(photo, destination=temp_input_path) 

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
    time_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d_%H-%M-%S")
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
    await callback.message.edit_text("✅Изображение готово.\n\nТеперь отправьте эмодзи для стикера (например: 😊 или 🔥🎉)")


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
    is_admin = await check_admin(session, user_id)
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
            await message.answer("✅ Стикер успешно добавлен в пак!", reply_markup=common_kb(is_admin))
            
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
        await message.answer(f"❌ Ошибка при добавлении стикера:\n{error_msg}", reply_markup=common_kb(is_admin))
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

@router.message(F.text == "➖Sticker")
async def handle_delete(message: Message, state: FSMContext, session:AsyncSession):
    user_id = message.from_user.id
    if not await check_access(session, user_id):
        await message.answer(
            "Вам не разрешено пользоваться ботом. \nИспользование бота разрешено семейству Кабалиных.\nОтправьте заявку на регистрацию.\nЕсли произошло недоразумение, обращайтесь @Vot_eto_rofl",
            parse_mode=None, reply_markup=register_kb()
        )
        return
    await state.set_state(Form.delete_sticker)
    await message.answer("Отправьте стикер, который хотите удалить.")


@router.message(Form.delete_sticker)
async def delete_sticker(message: Message, bot: Bot, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    sticker = message.sticker
    if not sticker:
        await message.answer("❌ Это не стикер! Попробуйте снова.", parse_mode=None)
        await state.clear()
        return
    sticker_set_name = sticker.set_name
    sticker_id = sticker.file_id

    if sticker_set_name != STICKER_SET_NAME:
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
    await message.answer(
        "Удалить этот стикер из набора?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="delete_sticker_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="delete_sticker_no"),
            ]
        ]),
    )


@router.callback_query(Form.delete_sticker_confirm, F.data == "delete_sticker_yes")
async def delete_sticker_confirm_yes(
    callback: CallbackQuery, bot: Bot, session: AsyncSession, state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    sticker_id = data.get("pending_delete_sticker_id")
    user_id = callback.from_user.id
    if not sticker_id:
        await callback.message.edit_text("❌ Сессия истекла. Выберите стикер заново (➖Sticker).")
        await state.clear()
        return
    try:
        result = await bot.delete_sticker_from_set(sticker=sticker_id)
    except Exception as e:
        await callback.message.edit_text(f"❌ Не удалось удалить стикер: {e}")
        await state.clear()
        return
    if result:
        await add_operation(
            session,
            SOperAdd(user_id=user_id, type_op="delete", sticker_id=sticker_id),
        )
        await callback.message.edit_text("✅ Стикер удалён из набора.")
        await callback.message.answer(
            "Ссылка на стикерпак\nhttps://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot\n\nУдачи :)"
        )
    await state.clear()


@router.callback_query(Form.delete_sticker_confirm, F.data == "delete_sticker_no")
async def delete_sticker_confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("❌Удаление отменено.")
    await state.clear()

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
            f"Привет {message.from_user.first_name}, вам разрешено пользоваться ботом.\n Бот управляет стикерпаком Кабалиных\nhttps://t.me/addstickers/qweasdzxc123_by_Stiker_durka_bot",
            parse_mode=None,
            reply_markup=common_kb(is_admin),
        )


@router.message(F.text == "➕ Добавить пользователя")
async def admin_add_user_start(message: Message, session: AsyncSession, state: FSMContext):
    if not await check_admin(session, message.from_user.id):
        return
    await state.set_state(Form.add_user)
    await message.answer(
        "Отправьте Telegram ID пользователя(обяз.), имя(необяз.), фамилию(необяз.) через запятую, в указаном порядке пользователя.\n"
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
    first_name = text[1] if len(text)>=2 else None
    last_name = text[2] if len(text)==3 else None
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
    await message.answer("Отправьте Telegram ID (число) или перешлите сообщение от пользователя.")


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
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_user_{u.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_user_{u.id}"),
            ]
        ])
        await message.answer(text, reply_markup=kb)


@router.message(F.text == "📝 Зарегистрироваться")
async def register_request(message: Message, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name if message.from_user.last_name else None
    username = (message.from_user.username or "—").strip()

    existing = await get_user_by_id(session, user_id)
    if existing:
        if existing.is_approved:
            await message.answer("Вы уже зарегистрированы!")
        else:
            await message.answer("Ваша заявка уже отправлена и ожидает подтверждения.")
        return

    new_user = UserModel(
        id=user_id,
        first_name=first_name,
        last_name=last_name,
        is_admin=False,
        is_approved=False,
    )
    session.add(new_user)
    await session.commit()

    admins = await get_all_admins(session)
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
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_user_{user_id}"),
                        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_user_{user_id}"),
                    ]
                ]),
            )
        except Exception as e:
            print(f"Не удалось отправить админу {admin.id}: {e}")

    await message.answer("✅ Заявка отправлена! Ожидайте подтверждения от администратора.")


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
        await callback.bot.send_message(user_id, "✅ Ваша заявка одобрена! Теперь вы можете пользоваться ботом.")
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