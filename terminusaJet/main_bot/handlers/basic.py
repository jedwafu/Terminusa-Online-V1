import requests

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import URL
from keyboards import reply, inline
from text import messages


router_basic = Router()


@router_basic.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    admin_info = requests.post(f"{URL}/api/bot/admin/{message.from_user.id}").json()

    await message.answer(
        "👋 Добро пожаловать",
        reply_markup=reply.main,
    )
    await message.answer_photo(
        "https://i2.wp.com/crashcasinos.com/wp-content/uploads/2020/08/crash-entry-cfec08.jpg",
        caption=messages.start_text(admin_info),
        reply_markup=inline.main_menu,
    )


@router_basic.message(F.text == "🚀 Меню")
async def menu_handler(message: Message) -> None:
    admin_info = requests.post(f"{URL}/api/bot/admin/{message.from_user.id}").json()

    await message.answer_photo(
        "https://i2.wp.com/crashcasinos.com/wp-content/uploads/2020/08/crash-entry-cfec08.jpg",
        caption=messages.start_text(admin_info),
        reply_markup=inline.main_menu,
    )
