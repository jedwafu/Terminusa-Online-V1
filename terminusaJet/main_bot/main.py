import sys, logging, asyncio

from aiogram import Bot, Dispatcher
from aiohttp import web

from config import TOKEN
from handlers.basic import router_basic
from handlers.callbacks import router_callbacks


bot = Bot(TOKEN)
dp = Dispatcher()


async def main():
    try:
        dp.include_router(router_basic)
        dp.include_router(router_callbacks)
        await dp.start_polling(bot, skip_updates=True)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("BOT EXIT")
