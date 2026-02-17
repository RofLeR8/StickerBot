"""Tests for start handlers (/start, /help, /cancel)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.start import cmd_start, cancel_operation, cmd_help


@pytest.fixture
def mock_message():
    """Create a mock message."""
    message = MagicMock(spec=Message)
    message.from_user = User(id=12345, first_name="Test", last_name="User", is_bot=False)
    message.answer = AsyncMock()
    return message


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
    return state


@pytest.mark.asyncio
async def test_cmd_start_approved_user(mock_message, mock_session, mock_state):
    """Test /start command for approved user."""
    with patch("handlers.start.check_access", return_value=True):
        with patch("handlers.start.check_admin", return_value=False):
            with patch("handlers.start.common_kb") as mock_kb:
                mock_kb.return_value = MagicMock()
                await cmd_start(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called_once()
    mock_state.clear.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "вам разрешено пользоваться ботом" in call_args


@pytest.mark.asyncio
async def test_cmd_start_admin_user(mock_message, mock_session, mock_state):
    """Test /start command for admin user."""
    with patch("handlers.start.check_access", return_value=True):
        with patch("handlers.start.check_admin", return_value=True):
            with patch("handlers.start.common_kb") as mock_kb:
                mock_kb.return_value = MagicMock()
                await cmd_start(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called_once()
    mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_cmd_start_unapproved_user(mock_message, mock_session, mock_state):
    """Test /start command for unapproved user."""
    with patch("handlers.start.check_access", return_value=False):
        with patch("handlers.start.register_kb") as mock_kb:
            mock_kb.return_value = MagicMock()
            await cmd_start(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Вам не разрешено пользоваться ботом" in call_args


@pytest.mark.asyncio
async def test_cmd_help_approved_user(mock_message, mock_session):
    """Test /help command for approved user."""
    with patch("handlers.start.check_access", return_value=True):
        with patch("handlers.start.support_keyboard") as mock_kb:
            mock_kb.return_value = MagicMock()
            await cmd_help(mock_message, mock_session)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "ошибки, баги или неисправности" in call_args


@pytest.mark.asyncio
async def test_cancel_operation_approved_user(mock_message, mock_session, mock_state):
    """Test /cancel command for approved user."""
    mock_state.get_data = AsyncMock(return_value={})
    with patch("handlers.start.check_access", return_value=True):
        with patch("handlers.start.check_admin", return_value=False):
            with patch("handlers.start.common_kb") as mock_kb:
                mock_kb.return_value = MagicMock()
                await cancel_operation(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called_once()
    assert "Операция отменена" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_cancel_operation_unapproved_user(mock_message, mock_session, mock_state):
    """Test /cancel command for unapproved user."""
    mock_state.get_data = AsyncMock(return_value={})
    with patch("handlers.start.check_access", return_value=False):
        with patch("handlers.start.register_kb") as mock_kb:
            mock_kb.return_value = MagicMock()
            await cancel_operation(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Операция отменена" in call_args


@pytest.mark.asyncio
async def test_cancel_operation_cleans_up_temp_files(mock_message, mock_session, mock_state):
    """Test /cancel command cleans up temporary files."""
    with patch("os.path.exists", return_value=True):
        with patch("os.unlink") as mock_unlink:
            mock_state.get_data = AsyncMock(return_value={
                "temp_photo_path": "/tmp/test.jpg",
                "sticker_path": "/tmp/test2.png",
            })
            with patch("handlers.start.check_access", return_value=True):
                with patch("handlers.start.check_admin", return_value=False):
                    with patch("handlers.start.common_kb"):
                        await cancel_operation(mock_message, mock_session, mock_state)

    assert mock_unlink.call_count == 2
