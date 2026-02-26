import logging
from aiogram import BaseMiddleware
from database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class DataBaseSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with AsyncSessionLocal() as session:
            data["session"] = session
            return await handler(event, data)
            