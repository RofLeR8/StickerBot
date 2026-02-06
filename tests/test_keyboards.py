"""Тесты клавиатур."""
import pytest
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup

from keyboards.reply import common_kb, admin_kb, register_kb
from keyboards.inline import (
    support_keyboard,
    choose_option_bg,
    skip_keywords_kb,
    user_action_kb,
    user_permissions_kb,
    user_delete_confirm_kb,
)


def test_common_kb_user():
    kb = common_kb(is_admin=False)
    assert isinstance(kb, ReplyKeyboardMarkup)
    assert kb.resize_keyboard is True
    # Две кнопки в первом ряду, без админ-панели
    rows = kb.keyboard
    assert len(rows) == 1
    assert any(b.text == "➕Sticker" for row in rows for b in row)
    assert any(b.text == "➖Sticker" for row in rows for b in row)


def test_common_kb_admin():
    kb = common_kb(is_admin=True)
    rows = kb.keyboard
    assert len(rows) == 2
    assert any(b.text == "⚙️Admin Panel" for row in rows for b in row)


def test_admin_kb():
    kb = admin_kb()
    assert isinstance(kb, ReplyKeyboardMarkup)
    texts = [b.text for row in kb.keyboard for b in row]
    assert "➕ Добавить пользователя" in texts
    assert "👥 Управление пользователями" in texts
    assert "📝 Список заявок" in texts
    assert "⬅️ В главное меню" in texts


def test_register_kb():
    kb = register_kb()
    assert isinstance(kb, ReplyKeyboardMarkup)
    texts = [b.text for row in kb.keyboard for b in row]
    assert "📝 Зарегистрироваться" in texts


def test_support_keyboard():
    kb = support_keyboard()
    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) >= 1


def test_choose_option_bg():
    kb = choose_option_bg()
    assert isinstance(kb, InlineKeyboardMarkup)
    buttons = [b for row in kb.inline_keyboard for b in row]
    assert any(b.callback_data == "remove_bg" for b in buttons)
    assert any(b.callback_data == "keep_bg" for b in buttons)


def test_skip_keywords_kb():
    kb = skip_keywords_kb()
    assert isinstance(kb, InlineKeyboardMarkup)
    assert any(b.callback_data == "skip_keywords" for row in kb.inline_keyboard for b in row)


def test_user_action_kb():
    kb = user_action_kb(123)
    assert isinstance(kb, InlineKeyboardMarkup)
    assert any(b.callback_data == "admin_del_123" for row in kb.inline_keyboard for b in row)
    assert any(b.callback_data == "admin_perm_123" for row in kb.inline_keyboard for b in row)


def test_user_permissions_kb():
    kb = user_permissions_kb(456, is_approved=True, is_admin=False)
    assert isinstance(kb, InlineKeyboardMarkup)
    assert any("perm_approve_" in (b.callback_data or "") for row in kb.inline_keyboard for b in row)
    assert any("perm_admin_" in (b.callback_data or "") for row in kb.inline_keyboard for b in row)
    assert any(b.callback_data == "admin_users_back" for row in kb.inline_keyboard for b in row)


def test_user_delete_confirm_kb():
    kb = user_delete_confirm_kb(789)
    assert isinstance(kb, InlineKeyboardMarkup)
    assert any("admin_del_confirm_789" in (b.callback_data or "") for row in kb.inline_keyboard for b in row)
    assert any(b.callback_data == "admin_del_cancel" for row in kb.inline_keyboard for b in row)
