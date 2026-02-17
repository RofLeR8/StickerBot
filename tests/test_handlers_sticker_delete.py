"""Tests for sticker delete handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Sticker
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from handlers.sticker_delete import (
    Form,
    handle_delete,
    delete_sticker,
    delete_sticker_confirm_yes,
    delete_sticker_confirm_no,
)


@pytest.fixture
def mock_message():
    """Create a mock message."""
    message = MagicMock(spec=Message)
    message.from_user = User(id=12345, first_name="Test", is_bot=False)
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_callback():
    """Create a mock callback query."""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = User(id=12345, first_name="Test", is_bot=False)
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
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
    bot.delete_sticker_from_set = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_handle_delete_unapproved_user(mock_message, mock_session, mock_state):
    """Test handle delete for unapproved user."""
    with patch("handlers.sticker_delete.check_access", return_value=False):
        with patch("handlers.sticker_delete.register_kb") as mock_kb:
            mock_kb.return_value = MagicMock()
            await handle_delete(mock_message, mock_state, mock_session)

    mock_message.answer.assert_called_once()
    assert "Вам не разрешено пользоваться ботом" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_delete_approved_user(mock_message, mock_session, mock_state):
    """Test handle delete for approved user."""
    with patch("handlers.sticker_delete.check_access", return_value=True):
        await handle_delete(mock_message, mock_state, mock_session)

    mock_state.set_state.assert_called_once_with(Form.delete_sticker)
    mock_message.answer.assert_called()
    assert "Отправьте стикер" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_delete_sticker_not_a_sticker(mock_message, mock_session, mock_state, mock_bot):
    """Test delete when message is not a sticker."""
    mock_message.sticker = None

    await delete_sticker(mock_message, mock_bot, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "Это не стикер" in mock_message.answer.call_args[0][0]
    mock_state.clear.assert_called()


@pytest.mark.asyncio
async def test_delete_sticker_wrong_set(mock_message, mock_session, mock_state, mock_bot):
    """Test delete when sticker is from wrong set."""
    sticker = MagicMock(spec=Sticker)
    sticker.set_name = "other_sticker_set"
    sticker.file_id = "sticker_123"
    mock_message.sticker = sticker

    with patch("handlers.sticker_delete.STICKER_SET_NAME", "my_sticker_set"):
        await delete_sticker(mock_message, mock_bot, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "не из вашего набора" in mock_message.answer.call_args[0][0]
    mock_state.clear.assert_called()


@pytest.mark.asyncio
async def test_delete_sticker_success(mock_message, mock_session, mock_state, mock_bot):
    """Test delete sticker successfully."""
    sticker = MagicMock(spec=Sticker)
    sticker.set_name = "my_sticker_set"
    sticker.file_id = "sticker_123"
    mock_message.sticker = sticker

    with patch("handlers.sticker_delete.STICKER_SET_NAME", "my_sticker_set"):
        await delete_sticker(mock_message, mock_bot, mock_session, mock_state)

    mock_state.update_data.assert_called_once_with(pending_delete_sticker_id="sticker_123")
    mock_state.set_state.assert_called_once_with(Form.delete_sticker_confirm)
    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_delete_sticker_confirm_yes_session_expired(mock_callback, mock_session, mock_state, mock_bot):
    """Test confirm delete when session is expired."""
    mock_state.get_data = AsyncMock(return_value={})

    await delete_sticker_confirm_yes(mock_callback, mock_bot, mock_session, mock_state)

    mock_callback.message.edit_text.assert_called()
    assert "Сессия истекла" in mock_callback.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_delete_sticker_confirm_yes_success(mock_callback, mock_session, mock_state, mock_bot):
    """Test confirm delete successfully."""
    mock_state.get_data = AsyncMock(return_value={"pending_delete_sticker_id": "sticker_123"})
    mock_bot.delete_sticker_from_set.return_value = True

    with patch("handlers.sticker_delete.add_operation"):
        await delete_sticker_confirm_yes(mock_callback, mock_bot, mock_session, mock_state)

    mock_bot.delete_sticker_from_set.assert_called_once_with(sticker="sticker_123")
    mock_callback.message.edit_text.assert_called()
    assert "Стикер удалён" in mock_callback.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_delete_sticker_confirm_yes_error(mock_callback, mock_session, mock_state, mock_bot):
    """Test confirm delete with API error."""
    mock_state.get_data = AsyncMock(return_value={"pending_delete_sticker_id": "sticker_123"})
    mock_bot.delete_sticker_from_set.side_effect = Exception("API Error")

    await delete_sticker_confirm_yes(mock_callback, mock_bot, mock_session, mock_state)

    mock_callback.message.edit_text.assert_called()
    assert "Не удалось удалить стикер" in mock_callback.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_delete_sticker_confirm_no(mock_callback, mock_state):
    """Test cancel delete."""
    await delete_sticker_confirm_no(mock_callback, mock_state)

    mock_callback.answer.assert_called()
    mock_callback.message.edit_text.assert_called()
    assert "Удаление отменено" in mock_callback.message.edit_text.call_args[0][0]
    mock_state.clear.assert_called()
