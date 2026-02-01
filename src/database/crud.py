from sqlalchemy.ext.asyncio import AsyncSession
from database.models import SUserAdd, SUserUpdate, SUserDelete, SOperAdd, SOperUpdate, SOperDelete
from database.schemas import UserModel, OperationModel

# User CRUD
async def add_user(session: AsyncSession, user: SUserAdd):
    db_user = UserModel(**user.model_dump())
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def update_user(session: AsyncSession, user: SUserUpdate):
    db_user = session.get(UserModel, user.id)
    if not db_user:
        raise ValueError("User not found")

    update_data = {k: v for k, v in user.model_dump().items() if v is not None}

    for key, value in update_data.items():
        setattr(db_user, key, value)

    await session.commit()
    await session.refresh(db_user)
    return db_user

async def delete_user(session: AsyncSession, user: SUserDelete):
    db_user = session.get(UserModel, user.id)
    if not db_user:
        raise ValueError("User not found")
    await session.delete(db_user)
    await session.commit()
    return True

async def get_user_by_id(session: AsyncSession, user_id: int):
    db_user = await session.get(UserModel, user_id)
    if not db_user:
        return None
    return db_user

async def check_access(session: AsyncSession, user_id: int):
    db_user = await get_user_by_id(session, user_id)
    return db_user is not None

async def check_admin(session: AsyncSession, user_id: int):
    db_user = await get_user_by_id(session, user_id)
    if db_user is None:
        return False
    return db_user.is_admin

# Operation CRUD
async def add_operation(session: AsyncSession, oper: SOperAdd):
    db_oper = OperationModel(**oper.model_dump())
    session.add(db_oper)
    await session.commit()
    await session.refresh(db_oper)
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
