import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import SUserAdd, SUserUpdate, SUserDelete, SOperAdd, SOperUpdate, SOperDelete
from database.schemas import UserModel, OperationModel

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# User CRUD
# -----------------------------------------------------------------------------
async def add_user(session: AsyncSession, user: SUserAdd):
    db_user = UserModel(**user.model_dump())
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    logger.info("User %d added to database", db_user.id)
    return db_user

async def update_user(session: AsyncSession, user: SUserUpdate):
    db_user = await session.get(UserModel, user.id)
    if not db_user:
        logger.error("User %d not found for update", user.id)
        raise ValueError("User not found")

    update_data = {k: v for k, v in user.model_dump().items() if k != "id" and v is not None}
    logger.debug("User %d update data: %s", user.id, update_data)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    await session.commit()
    await session.refresh(db_user)
    logger.info("User %d updated", user.id)
    return db_user

async def delete_user_by_id(session: AsyncSession, user_id: int):
    db_user = await session.get(UserModel, user_id)
    if not db_user:
        logger.error("User %d not found for deletion", user_id)
        raise ValueError("User not found")
    await session.delete(db_user)
    await session.commit()
    logger.info("User %d deleted from database", user_id)
    return True

async def get_user_by_id(session: AsyncSession, user_id: int):
    db_user = await session.get(UserModel, user_id)
    if not db_user:
        logger.debug("User %d not found", user_id)
        return None
    return db_user

async def get_all_admins(session: AsyncSession):
    stmt = select(UserModel).where(UserModel.is_admin == True)
    result = await session.scalars(stmt)
    return list(result.all())


async def get_all_users(session: AsyncSession):
    """Все пользователи (для админ-панели)."""
    stmt = select(UserModel).order_by(UserModel.id)
    result = await session.scalars(stmt)
    return list(result.all())


async def set_user_admin(session: AsyncSession, user_id: int, is_admin: bool):
    """Выдать или забрать права админа."""
    db_user = await session.get(UserModel, user_id)
    if not db_user:
        raise ValueError("User not found")
    db_user.is_admin = is_admin
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_pending_users(session: AsyncSession):
    """Пользователи с заявкой на регистрацию (is_approved=False), уже в таблице users."""
    stmt = select(UserModel).where(UserModel.is_approved == False)
    result = await session.scalars(stmt)
    return list(result.all())


async def set_user_approved(session: AsyncSession, user_id: int, approved: bool = True):
    """Одобрить или снять одобрение пользователя."""
    db_user = await session.get(UserModel, user_id)
    if not db_user:
        raise ValueError("User not found")
    db_user.is_approved = approved
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def check_access(session: AsyncSession, user_id: int):
    db_user = await get_user_by_id(session, user_id)
    has_access = db_user is not None and db_user.is_approved
    logger.debug("User %d access check: %s", user_id, has_access)
    return has_access

async def check_admin(session: AsyncSession, user_id: int) -> bool:
    db_user = await get_user_by_id(session, user_id)
    if db_user is None:
        return False
    return db_user.is_admin


# -----------------------------------------------------------------------------
# Operation CRUD
# -----------------------------------------------------------------------------

async def add_operation(session: AsyncSession, oper: SOperAdd):
    data = oper.model_dump()
    if data.get("created_at") is None:
        data["created_at"] = datetime.datetime.now()
    db_oper = OperationModel(**data)
    session.add(db_oper)
    await session.commit()
    await session.refresh(db_oper)
    logger.info("Operation logged: user_id=%d, type=%s", oper.user_id, oper.type_op)
    return db_oper


async def get_operation(session: AsyncSession, oper_id: int):
    return await session.get(OperationModel, oper_id)


async def update_operation(session: AsyncSession, oper: SOperUpdate):
    db_oper = await session.get(OperationModel, oper.id)
    if not db_oper:
        raise ValueError("Operation not found")

    update_data = {k: v for k, v in oper.model_dump().items() if k != "id" and v is not None}

    for key, value in update_data.items():
        setattr(db_oper, key, value)

    await session.commit()
    await session.refresh(db_oper)
    return db_oper


async def delete_operation(session: AsyncSession, oper: SOperDelete):
    db_oper = await session.get(OperationModel, oper.id)
    if not db_oper:
        raise ValueError("Operation not found")
    await session.delete(db_oper)
    await session.commit()
    return True


async def get_operations_paginated(session: AsyncSession, limit: int = 10, offset: int = 0):
    """Получить операции с пагинацией."""
    stmt = select(OperationModel).order_by(OperationModel.created_at.desc()).limit(limit).offset(offset)
    result = await session.scalars(stmt)
    return list(result.all())


async def get_operations_count(session: AsyncSession):
    """Получить общее количество операций."""
    from sqlalchemy import func
    stmt = select(func.count(OperationModel.id))
    result = await session.execute(stmt)
    return result.scalar()
