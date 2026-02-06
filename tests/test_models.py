"""Тесты Pydantic-моделей (схем)."""
import datetime
import pytest
from pydantic import ValidationError

from database.models import SUserAdd, SUserUpdate, SOperAdd, SOperUpdate, SOperDelete


def test_suser_add():
    u = SUserAdd(id=1, first_name="A", last_name="B", is_admin=False, is_approved=True)
    assert u.id == 1
    assert u.first_name == "A"
    assert u.model_dump()["id"] == 1

    u2 = SUserAdd(id=2)
    assert u2.first_name is None
    assert u2.is_admin is False


def test_suser_add_requires_id():
    with pytest.raises(ValidationError):
        SUserAdd(first_name="X")  # нет id


def test_soper_add():
    o = SOperAdd(user_id=10, type_op="add", sticker_id="file_abc")
    assert o.user_id == 10
    assert o.type_op == "add"
    assert o.sticker_id == "file_abc"
    assert o.created_at is None

    o2 = SOperAdd(user_id=11, type_op="delete", sticker_id="x", created_at=datetime.datetime.now())
    assert o2.created_at is not None


def test_soper_add_validation():
    with pytest.raises(ValidationError):
        SOperAdd(user_id=1, type_op="add")  # нет sticker_id
    with pytest.raises(ValidationError):
        SOperAdd(type_op="add", sticker_id="x")  # нет user_id


def test_soper_update():
    o = SOperUpdate(id=1, type_op="new_type")
    assert o.id == 1
    assert o.type_op == "new_type"
    assert o.user_id is None
    assert o.sticker_id is None


def test_soper_delete():
    o = SOperDelete(id=5)
    assert o.id == 5
