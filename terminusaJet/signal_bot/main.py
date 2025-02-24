import sys, logging, asyncio

from aiogram import Bot, Dispatcher

from config import TOKEN
from handlers.basic import router_basic
# from core.handlers.callbacks import router_callbacks


bot = Bot(TOKEN)
dp = Dispatcher()


async def main():
    try:
        dp.include_router(router_basic)
        # dp.include_router(router_callbacks)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("EXIT")
