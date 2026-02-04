from aiogram import Bot, Dispatcher
from aiogram.types import Message, BotCommand
from aiogram.filters import CommandStart
import os
from dotenv import load_dotenv
import asyncio
from argparse import ArgumentParser
from middlewares.middleware import DataBaseSessionMiddleware
from database.database import create_tables
from handlers.handler import router as handler
load_dotenv(dotenv_path="./src/.env")

dp = Dispatcher()
dp.message.middleware(DataBaseSessionMiddleware())
dp.callback_query.middleware(DataBaseSessionMiddleware())
dp.include_router(handler)
def get_token(mode: str) -> str:
    if mode ==  "dev":
        token = os.getenv("BOT_TOKEN_DEV")
    elif mode == "prod":
        token = os.getenv("BOT_TOKEN_PROD")
    else:
        raise ValueError("Mode must be 'dev' or 'prod'")
    if not token:
        raise RuntimeError(f"Token for mode '{mode}' not found in .env file. Check location and token")
    return token
# @dp.message(CommandStart())
# async def start_message(msg: Message):
#     await msg.answer(f"Hello,{msg.from_user.full_name}! The bot is currently unavailable while the admin is working on improving it. Sorry for the inconvenience.", parse_mode=None)
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запуск бота"),
        BotCommand(command="/help", description="Проблемы с ботом"),
        BotCommand(command="/cancel", description="Отменить текущую операцию")
    ]
    await bot.set_my_commands(commands)
async def main() -> None:
    #Parse CL arguments
    parser = ArgumentParser(description="Running tg-bot")
    parser.add_argument(
        "--mode",
        choices=["dev","prod"],
        required=True,
        help="Runnning mode: 'dev' for developing, 'prod' for production"
    )
    args = parser.parse_args()
    token = get_token(args.mode)
    # Initialize Bot instance 
    bot = Bot(token=token)
    await create_tables()
    await set_bot_commands(bot)

    # And the run events dispatching
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
