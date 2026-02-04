import datetime
from pydantic import BaseModel, ConfigDict


class SUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SUserAdd(SUser):
    id: int  # Telegram user id
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool = False
    is_approved: bool = False


class SUserUpdate(SUserAdd):
    id: int


class SUserDelete(SUser):
    id: int


class SOper(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SOperAdd(SOper):
    user_id: int
    type_op: str
    sticker_id: str
    created_at: datetime.datetime | None = None  # если не задано, подставится на бэкенде


class SOperUpdate(SOper):
    id: int
    user_id: int | None = None
    type_op: str | None = None
    sticker_id: str | None = None
    created_at: datetime.datetime | None = None


class SOperDelete(SOper):
    id: int
