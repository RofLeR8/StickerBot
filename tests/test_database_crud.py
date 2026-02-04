"""Тесты CRUD и доступа к БД."""
import pytest
import datetime

from database.crud import (
    add_user,
    get_user_by_id,
    get_all_admins,
    get_pending_users,
    set_user_approved,
    delete_user_by_id,
    check_access,
    check_admin,
    add_operation,
    get_operation,
)
from database.models import SUserAdd, SUserUpdate, SOperAdd


@pytest.mark.asyncio
async def test_add_user_and_get(db_session):
    user = await add_user(
        db_session,
        SUserAdd(id=12345, first_name="Test", last_name="User", is_admin=False, is_approved=True),
    )
    assert user.id == 12345
    assert user.first_name == "Test"
    assert user.is_approved is True

    found = await get_user_by_id(db_session, 12345)
    assert found is not None
    assert found.first_name == "Test"


@pytest.mark.asyncio
async def test_check_access_and_admin(db_session):
    await add_user(
        db_session,
        SUserAdd(id=1, first_name="A", is_admin=False, is_approved=True),
    )
    await add_user(
        db_session,
        SUserAdd(id=2, first_name="B", is_admin=True, is_approved=True),
    )
    await add_user(
        db_session,
        SUserAdd(id=3, first_name="C", is_admin=False, is_approved=False),
    )

    assert await check_access(db_session, 1) is True
    assert await check_access(db_session, 2) is True
    assert await check_access(db_session, 3) is False
    assert await check_access(db_session, 999) is False

    assert await check_admin(db_session, 1) is False
    assert await check_admin(db_session, 2) is True
    assert await check_admin(db_session, 999) is False


@pytest.mark.asyncio
async def test_get_pending_users(db_session):
    await add_user(db_session, SUserAdd(id=10, first_name="P", is_approved=False))
    await add_user(db_session, SUserAdd(id=11, first_name="Q", is_approved=True))

    pending = await get_pending_users(db_session)
    assert len(pending) == 1
    assert pending[0].id == 10


@pytest.mark.asyncio
async def test_set_user_approved(db_session):
    await add_user(db_session, SUserAdd(id=20, first_name="X", is_approved=False))
    assert await check_access(db_session, 20) is False

    await set_user_approved(db_session, 20, approved=True)
    u = await get_user_by_id(db_session, 20)
    assert u.is_approved is True
    assert await check_access(db_session, 20) is True


@pytest.mark.asyncio
async def test_delete_user_by_id(db_session):
    await add_user(db_session, SUserAdd(id=30, first_name="D", is_approved=True))
    await delete_user_by_id(db_session, 30)
    assert await get_user_by_id(db_session, 30) is None

    with pytest.raises(ValueError, match="User not found"):
        await delete_user_by_id(db_session, 99999)


@pytest.mark.asyncio
async def test_get_all_admins(db_session):
    await add_user(db_session, SUserAdd(id=40, first_name="Ad", is_admin=True, is_approved=True))
    await add_user(db_session, SUserAdd(id=41, first_name="Us", is_admin=False, is_approved=True))

    admins = await get_all_admins(db_session)
    assert len(admins) == 1
    assert admins[0].id == 40


@pytest.mark.asyncio
async def test_add_operation_and_get(db_session):
    await add_user(db_session, SUserAdd(id=100, first_name="Op", is_approved=True))
    oper = await add_operation(
        db_session,
        SOperAdd(user_id=100, type_op="add", sticker_id="file_123"),
    )
    assert oper.id is not None
    assert oper.user_id == 100
    assert oper.type_op == "add"
    assert oper.sticker_id == "file_123"
    assert oper.created_at is not None

    got = await get_operation(db_session, oper.id)
    assert got.type_op == "add"
    assert got.created_at is not None


@pytest.mark.asyncio
async def test_add_operation_sets_created_at(db_session):
    await add_user(db_session, SUserAdd(id=101, first_name="U", is_approved=True))
    before = datetime.datetime.now(datetime.UTC)
    oper = await add_operation(
        db_session,
        SOperAdd(user_id=101, type_op="delete", sticker_id="sticker_456"),
    )
    after = datetime.datetime.now(datetime.UTC)
    assert before <= oper.created_at <= after
