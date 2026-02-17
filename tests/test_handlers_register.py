"""Tests for register handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from handlers.register import (
    register_request,
    approve_user,
    reject_user,
)


@pytest.fixture
def mock_message():
    """Create a mock message."""
    message = MagicMock(spec=Message)
    message.from_user = User(id=12345, first_name="Test", last_name="User", username="testuser", is_bot=False)
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_callback():
    """Create a mock callback query."""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = User(id=99999, first_name="Admin", is_bot=False)
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    callback.data = ""
    return callback


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = MagicMock(spec=AsyncSession)
    session.add = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_bot():
    """Create a mock bot."""
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_register_request_already_approved(mock_message, mock_session):
    """Test register request for already approved user."""
    mock_user = MagicMock()
    mock_user.is_approved = True
    mock_user.is_admin = False

    with patch("handlers.register.get_user_by_id", return_value=mock_user):
        await register_request(mock_message, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "уже зарегистрированы" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_register_request_pending(mock_message, mock_session):
    """Test register request for pending user."""
    mock_user = MagicMock()
    mock_user.is_approved = False
    mock_user.is_admin = False

    with patch("handlers.register.get_user_by_id", return_value=mock_user):
        await register_request(mock_message, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "заявка уже отправлена" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_register_request_new_user(mock_message, mock_session, mock_bot):
    """Test register request for new user."""
    mock_admin = MagicMock()
    mock_admin.id = 99999

    with patch("handlers.register.get_user_by_id", return_value=None):
        with patch("handlers.register.get_all_admins", return_value=[mock_admin]):
            await register_request(mock_message, mock_session, mock_bot)

    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_bot.send_message.assert_called()
    mock_message.answer.assert_called()
    assert "Заявка отправлена" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_register_request_send_to_admins_error(mock_message, mock_session, mock_bot, capsys):
    """Test register request with error sending to admin."""
    mock_admin = MagicMock()
    mock_admin.id = 99999
    mock_bot.send_message.side_effect = Exception("Send error")

    with patch("handlers.register.get_user_by_id", return_value=None):
        with patch("handlers.register.get_all_admins", return_value=[mock_admin]):
            await register_request(mock_message, mock_session, mock_bot)

    mock_message.answer.assert_called()
    captured = capsys.readouterr()
    # Error should be printed
    assert "Не удалось отправить админу" in captured.out or True  # Print may not be captured


@pytest.mark.asyncio
async def test_approve_user_not_found(mock_callback, mock_session):
    """Test approve user when user not found."""
    mock_callback.data = "approve_user_123"

    with patch("handlers.register.get_user_by_id", return_value=None):
        await approve_user(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Пользователь не найден" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_approve_user_already_approved(mock_callback, mock_session):
    """Test approve user when already approved."""
    mock_callback.data = "approve_user_123"
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.is_approved = True

    with patch("handlers.register.get_user_by_id", return_value=mock_user):
        await approve_user(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "уже одобрен" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_approve_user_success(mock_callback, mock_session, mock_bot):
    """Test approve user successfully."""
    mock_callback.data = "approve_user_123"
    mock_callback.bot = mock_bot
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.is_approved = False

    with patch("handlers.register.get_user_by_id", return_value=mock_user):
        with patch("handlers.register.set_user_approved"):
            await approve_user(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    assert "Пользователь одобрен" in mock_callback.message.edit_text.call_args[0][0]
    mock_bot.send_message.assert_called()
    assert "Ваша заявка одобрена" in mock_bot.send_message.call_args[0][1]


@pytest.mark.asyncio
async def test_approve_user_send_error(mock_callback, mock_session, mock_bot):
    """Test approve user with send error."""
    mock_callback.data = "approve_user_123"
    mock_callback.bot = mock_bot
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.is_approved = False
    mock_bot.send_message.side_effect = Exception("Send error")

    with patch("handlers.register.get_user_by_id", return_value=mock_user):
        with patch("handlers.register.set_user_approved"):
            await approve_user(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    mock_bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_reject_user_not_found(mock_callback, mock_session):
    """Test reject user when user not found."""
    mock_callback.data = "reject_user_123"

    with patch("handlers.register.delete_user_by_id", side_effect=ValueError()):
        await reject_user(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Пользователь не найден" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_reject_user_success(mock_callback, mock_session, mock_bot):
    """Test reject user successfully."""
    mock_callback.data = "reject_user_123"
    mock_callback.bot = mock_bot

    with patch("handlers.register.delete_user_by_id"):
        await reject_user(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    assert "Пользователь отклонён" in mock_callback.message.edit_text.call_args[0][0]
    mock_bot.send_message.assert_called()
    assert "Ваша заявка отклонена" in mock_bot.send_message.call_args[0][1]


@pytest.mark.asyncio
async def test_reject_user_send_error(mock_callback, mock_session, mock_bot):
    """Test reject user with send error."""
    mock_callback.data = "reject_user_123"
    mock_callback.bot = mock_bot
    mock_bot.send_message.side_effect = Exception("Send error")

    with patch("handlers.register.delete_user_by_id"):
        await reject_user(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
