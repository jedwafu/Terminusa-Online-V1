import requests

from aiogram import Router, filters, F

from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery


from aiogram.enums import ParseMode

from config import URL
from keyboards import reply, inline
from texts import messages


router_basic = Router()


@router_basic.message(CommandStart(deep_link=True))
async def handler(message: Message, command: CommandObject):
    admin_id = command.args
    res = requests.post(f'{URL}/api/bot/admin/{admin_id}')
    promo = res.json()['word']
    requests.post(
        f"{URL}/api/bot/signal/{message.from_user.id}", json={"admin_id": admin_id}
    )
    await message.answer(
        messages.get_start_text1(promo),
        parse_mode=ParseMode.HTML,
        reply_markup=inline.main,
    )
    await message.answer(
        messages.start_text2,
        reply_markup=reply.main,
    )


@router_basic.message(F.text == "Получить сигнал🚀")
async def get_signal(message: Message) -> None:
    response = requests.get(f"{URL}/api/bot/signal/{message.from_user.id}")
    match response.status_code:
        case 200:
            signal = response.json()[0]
            await message.answer(
                f"""🆔 Идентификатор игры: {signal["id"]}
💸 Множитель: x{signal["multiplier"]}"""
            )
        case 400:
            await message.answer("❌ Вы уже получили сигнал для этой игры")
        case 403:
            await message.answer(
                """❌ Достигнут лимит сигналов на сегодня
    У нас есть реферальная система! Вы можете получать по одному сигналу за каждого приведенного друга, кликай кнопку ниже!"""
            )
        case 404:
            print("НЕТ ИГР")