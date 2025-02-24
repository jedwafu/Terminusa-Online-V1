import aiohttp
import aiohttp.web as web
import asyncio
import requests
from aiogram import Router, F, Bot

from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from config import *

bot = Bot(TOKEN)


async def handle(request):
    try:
        data = await request.json()
        depozite_id = str(data["id"])
        chat_id = data["chat_id"]
        nickname = data["user"]
        balance = data["amount"]

        message = f"""ℹ️ Мамонт <code>{nickname}</code> хочет пополнить баланс
└ Сумма: <code>{balance}</code> RUB"""

        await bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Оплатить",
                            callback_data="confirm_payed_" + depozite_id,
                        )
                    ],
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
        return web.json_response({"status": "success"}, status=200)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def init_app():
    app = web.Application()
    app.router.add_post("/balance", handle)
    return app


def main(bot):
    global _bot
    _bot = bot
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, host="0.0.0.0", port=5001)


if __name__ == "__main__":
    main(bot)
