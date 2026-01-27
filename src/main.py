from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
import os
from dotenv import load_dotenv
import asyncio
load_dotenv(dotenv_path="./src/.env")
TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

@dp.message(CommandStart())
async def start_message(msg: Message):
    await msg.answer(f"Hello,{msg.from_user.full_name}! The bot is currently unavailable while the admin is working on improving it. Sorry for the inconvenience.", parse_mode=None)

async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN)

    # And the run events dispatching
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())