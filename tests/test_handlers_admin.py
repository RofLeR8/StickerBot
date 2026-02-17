"""Tests for admin handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from handlers.admin import (
    Form,
    handle_admin_panel,
    admin_back_to_main,
    admin_add_user_start,
    admin_add_user_by_text,
    admin_add_user_other,
    admin_manage_users,
    admin_user_permissions,
    admin_toggle_approve,
    admin_toggle_admin,
    admin_users_back,
    admin_delete_user,
    admin_list_requests,
    admin_list_operations,
    show_operations_page,
    callback_operations_page,
    callback_operations_refresh,
    admin_get_sticker_by_file_id,
    admin_send_sticker_by_file_id,
)


@pytest.fixture
def mock_message():
    """Create a mock message."""
    message = MagicMock(spec=Message)
    message.from_user = User(id=12345, first_name="Test", is_bot=False)
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
    callback.message.answer = AsyncMock()
    callback.message.delete = AsyncMock()
    callback.answer = AsyncMock()
    callback.data = ""
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
    bot.send_message = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_handle_admin_panel_not_admin(mock_message, mock_session):
    """Test admin panel for non-admin user."""
    with patch("handlers.admin.check_admin", return_value=False):
        await handle_admin_panel(mock_message, mock_session)

    mock_message.answer.assert_called_once()
    assert "Вы не админ" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_admin_panel_admin(mock_message, mock_session):
    """Test admin panel for admin user."""
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.admin_kb") as mock_kb:
            mock_kb.return_value = MagicMock()
            await handle_admin_panel(mock_message, mock_session)

    mock_message.answer.assert_called()
    assert "Админ-панель" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_back_to_main(mock_message, mock_session, mock_state):
    """Test admin back to main menu."""
    with patch("handlers.admin.check_admin", return_value=False):
        with patch("handlers.admin.common_kb") as mock_kb:
            mock_kb.return_value = MagicMock()
            await admin_back_to_main(mock_message, mock_session, mock_state)

    mock_state.clear.assert_called()
    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_admin_add_user_start_not_admin(mock_message, mock_session, mock_state):
    """Test add user start for non-admin."""
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_add_user_start(mock_message, mock_session, mock_state)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_admin_add_user_start_admin(mock_message, mock_session, mock_state):
    """Test add user start for admin."""
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_add_user_start(mock_message, mock_session, mock_state)

    mock_state.set_state.assert_called_once_with(Form.add_user)
    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_admin_add_user_by_text_not_admin(mock_message, mock_session, mock_state):
    """Test add user by text for non-admin."""
    mock_message.text = "123, Test, User"
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_add_user_by_text(mock_message, mock_session, mock_state)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_admin_add_user_by_text_invalid_format(mock_message, mock_session, mock_state):
    """Test add user by text with invalid format."""
    mock_message.text = ", Test, User"
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_add_user_by_text(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "Неправильный формат" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_add_user_by_text_already_exists(mock_message, mock_session, mock_state):
    """Test add user by text when user exists."""
    mock_message.text = "123, Test, User"
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=MagicMock()):
            await admin_add_user_by_text(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "уже есть в базе" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_add_user_by_text_success(mock_message, mock_session, mock_state):
    """Test add user by text successfully."""
    mock_message.text = "123, Test, User"
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=None):
            with patch("handlers.admin.crud_add_user"):
                await admin_add_user_by_text(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "Пользователь добавлен" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_add_user_by_text_error(mock_message, mock_session, mock_state):
    """Test add user by text with error."""
    mock_message.text = "123, Test, User"
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=None):
            with patch("handlers.admin.crud_add_user", side_effect=Exception("DB Error")):
                await admin_add_user_by_text(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "Ошибка при добавлении" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_add_user_other_not_admin(mock_message, mock_session, mock_state):
    """Test add user other for non-admin."""
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_add_user_other(mock_message, mock_session, mock_state)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_admin_add_user_other_forward_exists(mock_message, mock_session, mock_state):
    """Test add user via forward when user exists."""
    mock_message.forward_from = User(id=999, first_name="Forward", is_bot=False)
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=MagicMock()):
            await admin_add_user_other(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "уже есть в базе" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_add_user_other_forward_success(mock_message, mock_session, mock_state):
    """Test add user via forward successfully."""
    mock_message.forward_from = User(id=999, first_name="Forward", is_bot=False)
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=None):
            with patch("handlers.admin.crud_add_user"):
                await admin_add_user_other(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "Пользователь добавлен" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_add_user_other_no_forward(mock_message, mock_session, mock_state):
    """Test add user without forward."""
    mock_message.forward_from = None
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_add_user_other(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "Отправьте Telegram ID" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_manage_users_not_admin(mock_message, mock_session):
    """Test manage users for non-admin."""
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_manage_users(mock_message, mock_session)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_admin_manage_users_no_users(mock_message, mock_session):
    """Test manage users with no users."""
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_all_users", return_value=[]):
            await admin_manage_users(mock_message, mock_session)

    mock_message.answer.assert_called()
    assert "нет пользователей" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_manage_users_with_users(mock_message, mock_session):
    """Test manage users with users list."""
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.is_admin = False
    mock_user.is_approved = True

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_all_users", return_value=[mock_user]):
            with patch("handlers.admin.user_action_kb") as mock_kb:
                mock_kb.return_value = MagicMock()
                await admin_manage_users(mock_message, mock_session)

    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_admin_manage_users_many_users(mock_message, mock_session):
    """Test manage users with more than 15 users."""
    mock_users = []
    for i in range(20):
        mock_user = MagicMock()
        mock_user.id = i
        mock_user.first_name = f"User{i}"
        mock_user.last_name = ""
        mock_user.is_admin = False
        mock_user.is_approved = True
        mock_users.append(mock_user)

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_all_users", return_value=mock_users):
            with patch("handlers.admin.user_action_kb", return_value=MagicMock()):
                await admin_manage_users(mock_message, mock_session)

    assert mock_message.answer.call_count == 16  # 15 users + 1 message for remaining


@pytest.mark.asyncio
async def test_admin_user_permissions_not_admin(mock_callback, mock_session):
    """Test user permissions for non-admin."""
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_user_permissions(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Нет доступа" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_user_permissions_user_not_found(mock_callback, mock_session):
    """Test user permissions when user not found."""
    mock_callback.data = "admin_perm_123"
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=None):
            await admin_user_permissions(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Пользователь не найден" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_user_permissions_success(mock_callback, mock_session):
    """Test user permissions successfully."""
    mock_callback.data = "admin_perm_123"
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.is_admin = False
    mock_user.is_approved = True

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=mock_user):
            with patch("handlers.admin.user_permissions_kb", return_value=MagicMock()):
                await admin_user_permissions(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    mock_callback.answer.assert_called()


@pytest.mark.asyncio
async def test_admin_toggle_approve_not_admin(mock_callback, mock_session):
    """Test toggle approve for non-admin."""
    mock_callback.data = "perm_approve_123_1"
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_toggle_approve(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Нет доступа" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_toggle_approve_user_not_found(mock_callback, mock_session):
    """Test toggle approve when user not found."""
    mock_callback.data = "perm_approve_123_1"
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=None):
            await admin_toggle_approve(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Пользователь не найден" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_toggle_approve_success(mock_callback, mock_session, mock_bot):
    """Test toggle approve successfully."""
    mock_callback.data = "perm_approve_123_1"
    mock_callback.bot = mock_bot
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.is_admin = False
    mock_user.is_approved = False

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=mock_user):
            with patch("handlers.admin.set_user_approved"):
                with patch("handlers.admin.user_permissions_kb", return_value=MagicMock()):
                    await admin_toggle_approve(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    mock_bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_admin_toggle_admin_not_admin(mock_callback, mock_session):
    """Test toggle admin for non-admin."""
    mock_callback.data = "perm_admin_123_1"
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_toggle_admin(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Нет доступа" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_toggle_admin_user_not_found(mock_callback, mock_session):
    """Test toggle admin when user not found."""
    mock_callback.data = "perm_admin_123_1"
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=None):
            await admin_toggle_admin(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Пользователь не найден" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_toggle_admin_success(mock_callback, mock_session, mock_bot):
    """Test toggle admin successfully."""
    mock_callback.data = "perm_admin_123_1"
    mock_callback.bot = mock_bot
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.is_admin = False
    mock_user.is_approved = True

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=mock_user):
            with patch("handlers.admin.set_user_admin"):
                with patch("handlers.admin.user_permissions_kb", return_value=MagicMock()):
                    await admin_toggle_admin(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    mock_bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_admin_users_back_not_admin(mock_callback, mock_session):
    """Test users back for non-admin."""
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_users_back(mock_callback, mock_session)

    mock_callback.answer.assert_called()


@pytest.mark.asyncio
async def test_admin_users_back_success(mock_callback, mock_session):
    """Test users back successfully."""
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_users_back(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    assert "Возврат" in mock_callback.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_delete_user_not_admin(mock_callback, mock_session):
    """Test delete user for non-admin."""
    mock_callback.data = "admin_del_123"
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_delete_user(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Нет доступа" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_delete_user_cancel(mock_callback, mock_session):
    """Test delete user cancel."""
    mock_callback.data = "admin_del_cancel"
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_delete_user(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    assert "Удаление отменено" in mock_callback.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_delete_user_confirm_not_found(mock_callback, mock_session):
    """Test delete user confirm when user not found."""
    mock_callback.data = "admin_del_confirm_123"
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=None):
            await admin_delete_user(mock_callback, mock_session)

    mock_callback.answer.assert_called()
    assert "Пользователь не найден" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_delete_user_confirm_success(mock_callback, mock_session, mock_bot):
    """Test delete user confirm successfully."""
    mock_callback.data = "admin_del_confirm_123"
    mock_callback.bot = mock_bot
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.first_name = "Test"
    mock_user.last_name = "User"

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=mock_user):
            with patch("handlers.admin.delete_user_by_id"):
                await admin_delete_user(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    assert "удалён" in mock_callback.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_delete_user_confirm_error(mock_callback, mock_session):
    """Test delete user confirm with error."""
    mock_callback.data = "admin_del_confirm_123"
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.first_name = "Test"
    mock_user.last_name = "User"

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=mock_user):
            with patch("handlers.admin.delete_user_by_id", side_effect=ValueError("Error")):
                await admin_delete_user(mock_callback, mock_session)

    mock_callback.answer.assert_called()


@pytest.mark.asyncio
async def test_admin_delete_user_show_confirm(mock_callback, mock_session):
    """Test delete user show confirmation."""
    mock_callback.data = "admin_del_123"
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.first_name = "Test"
    mock_user.last_name = "User"

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_user_by_id", return_value=mock_user):
            with patch("handlers.admin.user_delete_confirm_kb", return_value=MagicMock()):
                await admin_delete_user(mock_callback, mock_session)

    mock_callback.message.edit_text.assert_called()
    assert "Удалить пользователя" in mock_callback.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_list_requests_not_admin(mock_message, mock_session, mock_bot):
    """Test list requests for non-admin."""
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_list_requests(mock_message, mock_session, mock_bot)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_admin_list_requests_no_pending(mock_message, mock_session, mock_bot):
    """Test list requests with no pending."""
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_pending_users", return_value=[]):
            await admin_list_requests(mock_message, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "Заявок на регистрацию нет" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_list_requests_with_pending(mock_message, mock_session, mock_bot):
    """Test list requests with pending users."""
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.first_name = "Test"
    mock_user.last_name = "User"

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_pending_users", return_value=[mock_user]):
            await admin_list_requests(mock_message, mock_session, mock_bot)

    mock_message.answer.assert_called()
    assert "Заявка" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_list_operations_not_admin(mock_message, mock_session, mock_state):
    """Test list operations for non-admin."""
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_list_operations(mock_message, mock_session, mock_state)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_admin_list_operations_empty(mock_message, mock_session, mock_state):
    """Test list operations when empty."""
    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.get_operations_paginated", return_value=[]):
            with patch("handlers.admin.get_operations_count", return_value=0):
                await admin_list_operations(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "История операций пуста" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_show_operations_page(mock_message, mock_session, mock_state):
    """Test show operations page."""
    mock_op = MagicMock()
    mock_op.id = 1
    mock_op.user_id = 123
    mock_op.type_op = "add"
    mock_op.sticker_id = "sticker_123"
    mock_op.created_at = MagicMock()
    mock_op.created_at.strftime = MagicMock(return_value="01.01.2024 12:00")

    mock_user = MagicMock()
    mock_user.first_name = "Test"
    mock_user.last_name = "User"

    mock_msg = MagicMock()
    mock_msg.message_id = 42

    with patch("handlers.admin.get_operations_paginated", return_value=[mock_op]):
        with patch("handlers.admin.get_operations_count", return_value=1):
            with patch("handlers.admin.get_user_by_id", return_value=mock_user):
                with patch("handlers.admin.operations_pagination_kb", return_value=MagicMock()):
                    mock_state.get_data = AsyncMock(return_value={})
                    mock_message.answer = AsyncMock(return_value=mock_msg)
                    await show_operations_page(mock_message, mock_session, mock_state, page=1)

    mock_message.answer.assert_called()
    mock_state.update_data.assert_called_with(ops_message_id=42)


@pytest.mark.asyncio
async def test_show_operations_page_edit_existing(mock_message, mock_session, mock_state):
    """Test show operations page editing existing message."""
    mock_op = MagicMock()
    mock_op.id = 1
    mock_op.user_id = 123
    mock_op.type_op = "add"
    mock_op.sticker_id = "sticker_123"
    mock_op.created_at = MagicMock()
    mock_op.created_at.strftime = MagicMock(return_value="01.01.2024 12:00")

    mock_user = MagicMock()
    mock_user.first_name = "Test"
    mock_user.last_name = "User"

    mock_bot = MagicMock()
    mock_bot.edit_message_text = AsyncMock()

    with patch("handlers.admin.get_operations_paginated", return_value=[mock_op]):
        with patch("handlers.admin.get_operations_count", return_value=1):
            with patch("handlers.admin.get_user_by_id", return_value=mock_user):
                with patch("handlers.admin.operations_pagination_kb", return_value=MagicMock()):
                    mock_state.get_data = AsyncMock(return_value={"ops_message_id": 42})
                    mock_message.bot = mock_bot
                    await show_operations_page(mock_message, mock_session, mock_state, page=1)

    mock_bot.edit_message_text.assert_called()


@pytest.mark.asyncio
async def test_show_operations_page_edit_fallback(mock_message, mock_session, mock_state):
    """Test show operations page fallback when edit fails."""
    mock_op = MagicMock()
    mock_op.id = 1
    mock_op.user_id = 123
    mock_op.type_op = "add"
    mock_op.sticker_id = "sticker_123"
    mock_op.created_at = MagicMock()
    mock_op.created_at.strftime = MagicMock(return_value="01.01.2024 12:00")

    mock_user = MagicMock()
    mock_user.first_name = "Test"
    mock_user.last_name = "User"

    mock_msg = MagicMock()
    mock_msg.message_id = 42

    mock_bot = MagicMock()
    mock_bot.edit_message_text = AsyncMock(side_effect=Exception())

    with patch("handlers.admin.get_operations_paginated", return_value=[mock_op]):
        with patch("handlers.admin.get_operations_count", return_value=1):
            with patch("handlers.admin.get_user_by_id", return_value=mock_user):
                with patch("handlers.admin.operations_pagination_kb", return_value=MagicMock()):
                    mock_state.get_data = AsyncMock(return_value={"ops_message_id": 42})
                    mock_message.bot = mock_bot
                    mock_message.answer = AsyncMock(return_value=mock_msg)
                    await show_operations_page(mock_message, mock_session, mock_state, page=1)

    mock_bot.edit_message_text.assert_called()
    mock_message.answer.assert_called()
    mock_state.update_data.assert_called_with(ops_message_id=42)


@pytest.mark.asyncio
async def test_callback_operations_page_not_admin(mock_callback, mock_session, mock_state):
    """Test callback operations page for non-admin."""
    mock_callback.data = "ops_page_2"
    with patch("handlers.admin.check_admin", return_value=False):
        await callback_operations_page(mock_callback, mock_session, mock_state)

    mock_callback.answer.assert_called()
    assert "Нет доступа" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_callback_operations_page_success(mock_callback, mock_session, mock_state):
    """Test callback operations page successfully."""
    mock_callback.data = "ops_page_2"
    mock_state.get_data = AsyncMock(return_value={"ops_message_id": None})

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.show_operations_page"):
            await callback_operations_page(mock_callback, mock_session, mock_state)

    mock_callback.answer.assert_called()


@pytest.mark.asyncio
async def test_callback_operations_refresh_not_admin(mock_callback, mock_session, mock_state):
    """Test callback operations refresh for non-admin."""
    mock_callback.data = "ops_refresh"
    with patch("handlers.admin.check_admin", return_value=False):
        await callback_operations_refresh(mock_callback, mock_session, mock_state)

    mock_callback.answer.assert_called()
    assert "Нет доступа" in mock_callback.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_callback_operations_refresh_success(mock_callback, mock_session, mock_state):
    """Test callback operations refresh successfully."""
    mock_callback.data = "ops_refresh"
    mock_state.get_data = AsyncMock(return_value={"ops_message_id": None})

    with patch("handlers.admin.check_admin", return_value=True):
        with patch("handlers.admin.show_operations_page"):
            await callback_operations_refresh(mock_callback, mock_session, mock_state)

    mock_callback.answer.assert_called()


@pytest.mark.asyncio
async def test_admin_get_sticker_by_file_id_not_admin(mock_message, mock_session, mock_state):
    """Test get sticker by file_id for non-admin."""
    mock_message.text = "🔍 Найти стикер"
    with patch("handlers.admin.check_admin", return_value=False):
        await admin_get_sticker_by_file_id(mock_message, mock_session, mock_state)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_admin_get_sticker_by_file_id_request(mock_message, mock_session, mock_state):
    """Test get sticker by file_id request from admin."""
    mock_message.text = "🔍 Найти стикер"
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_get_sticker_by_file_id(mock_message, mock_session, mock_state)

    mock_message.answer.assert_called()
    assert "Отправьте file_id" in mock_message.answer.call_args[0][0]
    mock_state.set_state.assert_called_with(Form.get_sticker_file_id)


@pytest.mark.asyncio
async def test_admin_send_sticker_by_file_id_success(mock_message, mock_session, mock_state, mock_bot):
    """Test send sticker by file_id successfully."""
    mock_message.text = "AgADAT123..."
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_send_sticker_by_file_id(mock_message, mock_session, mock_state, mock_bot)

    mock_bot.send_sticker.assert_called_with(chat_id=mock_message.chat.id, sticker="AgADAT123...")
    mock_message.answer.assert_called()
    assert "Стикер найден" in mock_message.answer.call_args[0][0]
    mock_state.clear.assert_called()


@pytest.mark.asyncio
async def test_admin_send_sticker_by_file_id_invalid(mock_message, mock_session, mock_state, mock_bot):
    """Test send sticker by file_id when invalid."""
    mock_message.text = "invalid_file_id"
    mock_bot.send_sticker = AsyncMock(side_effect=Exception("STICKER_DOCUMENT_INVALID"))
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_send_sticker_by_file_id(mock_message, mock_session, mock_state, mock_bot)

    mock_message.answer.assert_called()
    assert "Стикер не найден или удалён" in mock_message.answer.call_args[0][0]
    mock_state.clear.assert_called()


@pytest.mark.asyncio
async def test_admin_send_sticker_by_file_id_empty(mock_message, mock_session, mock_state, mock_bot):
    """Test send sticker by file_id with empty file_id."""
    mock_message.text = "   "
    with patch("handlers.admin.check_admin", return_value=True):
        await admin_send_sticker_by_file_id(mock_message, mock_session, mock_state, mock_bot)

    mock_message.answer.assert_called()
    assert "Пустой file_id" in mock_message.answer.call_args[0][0]
