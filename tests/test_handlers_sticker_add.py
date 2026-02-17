"""Tests for sticker add handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from aiogram.types import Message, CallbackQuery, User, PhotoSize, Sticker
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from handlers.sticker_add import (
    Form,
    is_valid_sticker_emoji,
    add_sticker,
    handle_photo,
    handle_sticker,
    process_choice,
    handle_emoji,
    handle_keywords,
    skip_keywords_callback,
    finish_sticker_creation,
)


@pytest.fixture
def mock_message():
    """Create a mock message."""
    user = User(id=12345, first_name="Test", is_bot=False)
    message = MagicMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 12345
    message.text = ""
    return message


@pytest.fixture
def mock_callback():
    """Create a mock callback query."""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = User(id=12345, first_name="Test", is_bot=False)
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def mock_state():
    """Create a mock FSM state."""
    state = MagicMock(spec=FSMContext)
    state.clear = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    return state


@pytest.fixture
def mock_bot():
    """Create a mock bot."""
    bot = MagicMock(spec=Bot)
    bot.download = AsyncMock()
    bot.get_file = AsyncMock()
    bot.add_sticker_to_set = AsyncMock()
    bot.get_sticker_set = AsyncMock()
    bot.send_sticker = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


class TestIsValidStickerEmoji:
    """Tests for is_valid_sticker_emoji function."""

    def test_valid_single_emoji(self):
        assert is_valid_sticker_emoji("😊") is True
        assert is_valid_sticker_emoji("🔥") is True

    def test_valid_multiple_emojis(self):
        assert is_valid_sticker_emoji("🔥🎉") is True
        assert is_valid_sticker_emoji("😀😃😄") is True

    def test_invalid_text_with_letters(self):
        assert is_valid_sticker_emoji("hello") is False
        assert is_valid_sticker_emoji("😊abc") is False

    def test_invalid_text_with_numbers(self):
        assert is_valid_sticker_emoji("123") is False
        assert is_valid_sticker_emoji("😊123") is False

    def test_empty_string(self):
        assert is_valid_sticker_emoji("") is False
        assert is_valid_sticker_emoji("   ") is False


@pytest.mark.asyncio
async def test_add_sticker_unapproved_user(mock_message, mock_session, mock_state):
    """Test add sticker for unapproved user."""
    with patch("handlers.sticker_add.check_access", return_value=False):
        with patch("handlers.sticker_add.register_kb") as mock_kb:
            mock_kb.return_value = MagicMock()
            await add_sticker(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called_once()
    assert "Вам не разрешено пользоваться ботом" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_add_sticker_approved_user(mock_message, mock_session, mock_state):
    """Test add sticker for approved user."""
    with patch("handlers.sticker_add.check_access", return_value=True):
        await add_sticker(mock_message, mock_session, mock_state)

    mock_state.set_state.assert_called_once_with(Form.choose_image)
    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_handle_photo_unapproved_user(mock_message, mock_session, mock_state, mock_bot):
    """Test handle photo for unapproved user."""
    mock_message.photo = [MagicMock(spec=PhotoSize)]
    with patch("handlers.sticker_add.check_access", return_value=False):
        with patch("handlers.sticker_add.register_kb") as mock_kb:
            mock_kb.return_value = MagicMock()
            await handle_photo(mock_message, mock_state, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "Вам не разрешено пользоваться ботом" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_photo_approved_user(mock_message, mock_session, mock_state, mock_bot):
    """Test handle photo for approved user."""
    photo = MagicMock(spec=PhotoSize)
    mock_message.photo = [photo]

    with patch("handlers.sticker_add.check_access", return_value=True):
        with patch("handlers.sticker_add.choose_option_bg") as mock_kb:
            mock_kb.return_value = MagicMock()
            await handle_photo(mock_message, mock_state, mock_session, mock_bot)

    mock_bot.download.assert_called_once()
    mock_state.update_data.assert_called_once()
    mock_state.set_state.assert_called_once_with(Form.choose_option)


@pytest.mark.asyncio
async def test_handle_sticker_animated(mock_message, mock_session, mock_state, mock_bot):
    """Test handle animated sticker (should be rejected)."""
    sticker = MagicMock(spec=Sticker)
    sticker.is_animated = True
    sticker.is_video = False
    mock_message.sticker = sticker

    with patch("handlers.sticker_add.check_access", return_value=True):
        await handle_sticker(mock_message, mock_state, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "Поддерживаются только статичные стикеры" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_sticker_video(mock_message, mock_session, mock_state, mock_bot):
    """Test handle video sticker (should be rejected)."""
    sticker = MagicMock(spec=Sticker)
    sticker.is_animated = False
    sticker.is_video = True
    mock_message.sticker = sticker

    with patch("handlers.sticker_add.check_access", return_value=True):
        await handle_sticker(mock_message, mock_state, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "Поддерживаются только статичные стикеры" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_sticker_success(mock_message, mock_session, mock_state, mock_bot):
    """Test handle static sticker successfully."""
    sticker = MagicMock(spec=Sticker)
    sticker.is_animated = False
    sticker.is_video = False
    sticker.file_id = "sticker_123"
    mock_message.sticker = sticker

    mock_file = MagicMock()
    mock_bot.get_file.return_value = mock_file

    with patch("handlers.sticker_add.check_access", return_value=True):
        with patch("handlers.sticker_add.resize_image"):
            await handle_sticker(mock_message, mock_state, mock_session, mock_bot)

    mock_bot.download.assert_called_once()
    mock_state.update_data.assert_called()
    mock_state.set_state.assert_called_once_with(Form.choose_emoji)


@pytest.mark.asyncio
async def test_process_choice_file_lost(mock_callback, mock_state):
    """Test process choice when file is lost."""
    mock_state.get_data = AsyncMock(return_value={"temp_photo_path": "/nonexistent.jpg"})

    await process_choice(mock_callback, mock_state)

    mock_callback.message.edit_text.assert_called()
    assert "файл утерян" in mock_callback.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_process_choice_keep_bg(mock_callback, mock_state):
    """Test process choice keeping background."""
    mock_state.get_data = AsyncMock(return_value={"temp_photo_path": "/tmp/test.jpg"})
    mock_callback.data = "keep_bg"

    with patch("os.path.exists", return_value=True):
        with patch("handlers.sticker_add.resize_image"):
            with patch("os.unlink"):
                await process_choice(mock_callback, mock_state)

    mock_state.set_state.assert_called_once_with(Form.choose_emoji)


@pytest.mark.asyncio
async def test_process_choice_remove_bg(mock_callback, mock_state):
    """Test process choice removing background."""
    mock_state.get_data = AsyncMock(return_value={"temp_photo_path": "/tmp/test.jpg"})
    mock_callback.data = "remove_bg"

    with patch("os.path.exists", return_value=True):
        with patch("handlers.sticker_add.resize_image"):
            with patch("handlers.sticker_add.remove_background"):
                with patch("os.unlink"):
                    await process_choice(mock_callback, mock_state)

    mock_state.set_state.assert_called_once_with(Form.choose_emoji)


@pytest.mark.asyncio
async def test_handle_emoji_empty(mock_message, mock_state):
    """Test handle empty emoji."""
    mock_message.text = "   "

    await handle_emoji(mock_message, mock_state)

    mock_message.answer.assert_called()
    assert "отправьте эмодзи" in mock_message.answer.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_handle_emoji_invalid(mock_message, mock_state):
    """Test handle invalid emoji with text."""
    mock_message.text = "hello"

    await handle_emoji(mock_message, mock_state)

    mock_message.answer.assert_called()
    assert "Некорректный ввод" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_emoji_too_long(mock_message, mock_state):
    """Test handle emoji that's too long."""
    mock_message.text = "😊" * 25

    await handle_emoji(mock_message, mock_state)

    mock_message.answer.assert_called()
    assert "Слишком много эмодзи" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_emoji_valid(mock_message, mock_state):
    """Test handle valid emoji."""
    mock_message.text = "😊"

    with patch("handlers.sticker_add.skip_keywords_kb") as mock_kb:
        mock_kb.return_value = MagicMock()
        await handle_emoji(mock_message, mock_state)

    mock_state.update_data.assert_called_once()
    mock_state.set_state.assert_called_once_with(Form.choose_keywords)


@pytest.mark.asyncio
async def test_handle_keywords_too_many(mock_message, mock_session, mock_state, mock_bot):
    """Test handle too many keywords."""
    mock_message.text = ",".join([f"word{i}" for i in range(25)])

    await handle_keywords(mock_message, mock_state, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "Слишком много ключевых слов" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_keywords_too_long_word(mock_message, mock_session, mock_state, mock_bot):
    """Test handle keyword that's too long."""
    mock_message.text = "a" * 70

    await handle_keywords(mock_message, mock_state, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "не длиннее 64 символов" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_keywords_valid(mock_message, mock_session, mock_state, mock_bot):
    """Test handle valid keywords."""
    mock_message.text = "cat, dog, pet"

    with patch("handlers.sticker_add.finish_sticker_creation"):
        await handle_keywords(mock_message, mock_state, mock_session, mock_bot)

    mock_state.update_data.assert_called()


@pytest.mark.asyncio
async def test_skip_keywords_callback(mock_callback, mock_session, mock_state, mock_bot):
    """Test skip keywords callback."""
    with patch("handlers.sticker_add.finish_sticker_creation"):
        await skip_keywords_callback(mock_callback, mock_state, mock_session, mock_bot)

    mock_callback.answer.assert_called()
    mock_state.update_data.assert_called_once_with(sticker_keywords="")


@pytest.mark.asyncio
async def test_finish_sticker_creation_file_lost(mock_message, mock_session, mock_state, mock_bot):
    """Test finish creation when file is lost."""
    mock_state.get_data = AsyncMock(return_value={"sticker_path": "/nonexistent.png"})

    with patch("handlers.sticker_add.check_admin", return_value=False):
        await finish_sticker_creation(mock_message, mock_state, mock_session, mock_bot, 12345)

    mock_message.answer.assert_called()
    assert "стикер утерян" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_finish_sticker_creation_success(mock_message, mock_session, mock_state, mock_bot):
    """Test finish creation successfully."""
    mock_state.get_data = AsyncMock(return_value={
        "sticker_path": "/tmp/test.png",
        "sticker_emoji": "😊",
        "sticker_keywords": ["cat"],
    })

    mock_sticker_set = MagicMock()
    mock_sticker = MagicMock()
    mock_sticker.file_id = "new_sticker_id"
    mock_sticker_set.stickers = [mock_sticker]
    mock_bot.get_sticker_set.return_value = mock_sticker_set

    with patch("os.path.exists", return_value=True):
        with patch("handlers.sticker_add.check_admin", return_value=False):
            with patch("handlers.sticker_add.add_operation"):
                with patch("handlers.sticker_add.FSInputFile"):
                    with patch("handlers.sticker_add.InputSticker"):
                        mock_bot.add_sticker_to_set.return_value = True
                        await finish_sticker_creation(
                            mock_message, mock_state, mock_session, mock_bot, 12345
                        )

    mock_bot.add_sticker_to_set.assert_called()
    mock_bot.send_sticker.assert_called()


@pytest.mark.asyncio
async def test_finish_sticker_creation_error(mock_message, mock_session, mock_state, mock_bot):
    """Test finish creation with error."""
    mock_state.get_data = AsyncMock(return_value={
        "sticker_path": "/tmp/test.png",
        "sticker_emoji": "😊",
    })

    mock_sticker_set = MagicMock()
    mock_sticker = MagicMock()
    mock_sticker.file_id = "error_sticker_id"
    mock_sticker_set.stickers = [mock_sticker]
    mock_bot.get_sticker_set.return_value = mock_sticker_set

    with patch("os.path.exists", return_value=True):
        with patch("handlers.sticker_add.check_admin", return_value=False):
            with patch("handlers.sticker_add.add_operation"):
                with patch("handlers.sticker_add.FSInputFile"):
                    with patch("handlers.sticker_add.InputSticker"):
                        mock_bot.add_sticker_to_set.side_effect = Exception("API Error")
                        await finish_sticker_creation(
                            mock_message, mock_state, mock_session, mock_bot, 12345
                        )

    mock_message.answer.assert_called()
    assert "Ошибка при добавлении стикера" in mock_message.answer.call_args[0][0]
