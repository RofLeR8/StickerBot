import os
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv
from database.schemas import Base

logger = logging.getLogger(__name__)

load_dotenv("./src/.env")

DATABASE_URL = os.getenv("DATABASE_URL")
logger.info("Database URL configured: %s", DATABASE_URL[:20] + "..." if DATABASE_URL else "None")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def create_tables():
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


