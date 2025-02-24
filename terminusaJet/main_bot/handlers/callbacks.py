import requests

from aiogram import Router, filters, F

from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import URL
from keyboards import inline, inline_builders
from text import messages


router_callbacks = Router()


class SettingWebsite(StatesGroup):
    message: Message
    min_deposit = State()
    min_output = State()
    stop_limit = State()
    referal_promocode = State()
    referal_percent = State()


class SettingBot(StatesGroup):
    message: Message
    massive_sendler = State()
    count_signals = State()
    support_bot = State()


class CreatePromo(StatesGroup):
    message: Message
    type: None
    nominal = State()
    count_activations = State()
    promo = State()


class MammothEditBalance(StatesGroup):
    message: Message
    user_id: None
    method_of_edit: None
    sum_edit = State()
    login_mammoth_on_site = State()


class BotAdd(StatesGroup):
    message: Message
    token = State()


class SiteAdd(StatesGroup):
    message: Message
    info = State()


@router_callbacks.callback_query(F.data == "pluger")
async def main_menu(callback: CallbackQuery) -> None:
    await callback.answer("Успешно изменено!")


@router_callbacks.callback_query(F.data == "plug")
async def main_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="Zаглушка",
        reply_markup=inline.plug,
    )


@router_callbacks.callback_query(F.data.contains("confirm_payed_"))
async def confirm_payed(callback: CallbackQuery) -> None:
    depozite_id = str(callback.data).split("_")[-1]
    requests.patch(f"{URL}//api/deposit/{depozite_id}")
    await callback.answer("Успешное пополнение!")
    await callback.message.delete()


@router_callbacks.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery) -> None:
    admin_info = requests.post(f"{URL}/api/bot/admin/{callback.from_user.id}").json()

    await callback.message.edit_caption(
        caption=messages.start_text(admin_info),
        reply_markup=inline.main_menu,
    )


# MAMMOTH MANAGEMENT - brench


@router_callbacks.callback_query(F.data == "mammoth_management")
async def mammoth_management(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="Управление мамонтом 🦣", reply_markup=inline.mammoth_management
    )


@router_callbacks.callback_query(F.data == "mammoth_on_site")
async def mammoth_on_site(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="Выберите мамонта",
        reply_markup=inline_builders.get_clava_mammoth_on_site(callback.from_user.id),
    )


@router_callbacks.callback_query(F.data.contains("management_user_"))
async def management_user(callback: CallbackQuery) -> None:
    user_id = str(callback.data).split("_")[-1]
    MammothEditBalance.user_id = user_id
    user_info = requests.get(f"{URL}/api/bot/userinfo/{user_id}").json()
    await callback.message.edit_caption(
        caption=messages.configure_user_info(user_info),
        reply_markup=inline_builders.get_clava_management_user(user_info),
    )


#


@router_callbacks.callback_query(F.data == "mammoth_edit_balance")
async def mammoth_edit_balance(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="💸 Выберите тип пополнения",
        reply_markup=inline.mammoth_edit_balance,
    )


@router_callbacks.callback_query(F.data == "mammoth_top_up_amount")
async def mammoth_edit_balance(callback: CallbackQuery, state: FSMContext) -> None:
    MammothEditBalance.message = callback.message
    MammothEditBalance.method_of_edit = "mammoth_top_up_amount"
    await state.set_state(MammothEditBalance.sum_edit)
    await callback.message.edit_caption(caption="💰 Введите сумму")


@router_callbacks.callback_query(F.data == "mammoth_withdraw_amount")
async def mammoth_edit_balance(callback: CallbackQuery, state: FSMContext) -> None:
    MammothEditBalance.message = callback.message
    MammothEditBalance.method_of_edit = "mammoth_withdraw_amount"
    await state.set_state(MammothEditBalance.sum_edit)
    await callback.message.edit_caption(caption="💰 Введите сумму")


@router_callbacks.callback_query(F.data == "mammoth_remove_balance")
async def mammoth_edit_balance(callback: CallbackQuery) -> None:
    requests.delete(f"{URL}/api/bot/balance/{MammothEditBalance.user_id}")
    user_info = requests.get(
        f"{URL}/api/bot/userinfo/{MammothEditBalance.user_id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_user_info(user_info),
        reply_markup=inline_builders.get_clava_management_user(user_info),
    )
    await callback.answer(text="Баланс успешно снят")


@router_callbacks.message(MammothEditBalance.sum_edit)
async def mammoth_edit_balance(message: Message, state: FSMContext) -> None:
    await message.delete()
    if str(message.text).isnumeric():
        if int(message.text) > 1:
            if int(message.text) < 1000000:
                match MammothEditBalance.method_of_edit:
                    case "mammoth_top_up_amount":
                        await state.update_data(sum_edit=message.text)
                        requests.post(
                            f"{URL}/api/bot/balance/{MammothEditBalance.user_id}",
                            json={"amount": (await state.get_data())["sum_edit"]},
                        )
                        user_info = requests.get(
                            f"{URL}/api/bot/userinfo/{MammothEditBalance.user_id}"
                        ).json()
                        await MammothEditBalance.message.edit_caption(
                            caption=messages.configure_user_info(user_info),
                            reply_markup=inline_builders.get_clava_management_user(
                                user_info
                            ),
                        )
                        await state.clear()
                    case "mammoth_withdraw_amount":
                        await state.update_data(sum_edit=message.text)
                        requests.put(
                            f"{URL}/api/bot/balance/{MammothEditBalance.user_id}",
                            json={"amount": (await state.get_data())["sum_edit"]},
                        )
                        user_info = requests.get(
                            f"{URL}/api/bot/userinfo/{MammothEditBalance.user_id}"
                        ).json()
                        await MammothEditBalance.message.edit_caption(
                            caption=messages.configure_user_info(user_info),
                            reply_markup=inline_builders.get_clava_management_user(
                                user_info
                            ),
                        )
                        await state.clear()

            else:
                await MammothEditBalance.message.edit_caption(
                    caption="❌ Сумма не должна быть больше 1 000 000 RUB\n\n💰 Введите сумму",
                )
        else:
            await MammothEditBalance.message.edit_caption(
                caption="❌ Сумма не должна быть меньше 1 RUB\n\n💰 Введите сумму",
            )
    else:
        await MammothEditBalance.message.edit_caption(
            caption="❌ Сумма должна быть целым числом\n\n💰 Введите сумму",
        )


#


@router_callbacks.callback_query(F.data == "mammoth_change_payout_method")
async def mammoth_change_payout_method(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/changeuser/{MammothEditBalance.user_id}",
        json={"action": "payout_method"},
    )
    user_info = requests.get(
        f"{URL}/api/bot/userinfo/{MammothEditBalance.user_id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_user_info(user_info),
        reply_markup=inline_builders.get_clava_management_user(user_info),
    )


@router_callbacks.callback_query(F.data == "mammoth_block_payout")
async def mammoth_block_payout(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/changeuser/{MammothEditBalance.user_id}",
        json={"action": "block_payout"},
    )
    user_info = requests.get(
        f"{URL}/api/bot/userinfo/{MammothEditBalance.user_id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_user_info(user_info),
        reply_markup=inline_builders.get_clava_management_user(user_info),
    )


@router_callbacks.callback_query(F.data == "mammoth_block_bet")
async def mammoth_block_bet(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/changeuser/{MammothEditBalance.user_id}",
        json={"action": "block_bet"},
    )
    user_info = requests.get(
        f"{URL}/api/bot/userinfo/{MammothEditBalance.user_id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_user_info(user_info),
        reply_markup=inline_builders.get_clava_management_user(user_info),
    )


@router_callbacks.callback_query(F.data == "mammoth_change_verification")
async def mammoth_change_verification(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/changeuser/{MammothEditBalance.user_id}",
        json={"action": "verification"},
    )
    user_info = requests.get(
        f"{URL}/api/bot/userinfo/{MammothEditBalance.user_id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_user_info(user_info),
        reply_markup=inline_builders.get_clava_management_user(user_info),
    )


@router_callbacks.callback_query(F.data == "mammoth_delete")
async def mammoth_delete(callback: CallbackQuery) -> None:
    requests.delete(f"{URL}/api/bot/changeuser/{MammothEditBalance.user_id}")
    await callback.message.edit_caption(
        caption="Управление мамонтом 🦣", reply_markup=inline.mammoth_management
    )


###


@router_callbacks.callback_query(F.data == "mammoth_add")
async def mammoth_add(callback: CallbackQuery, state: FSMContext) -> None:
    MammothEditBalance.message = callback.message
    await callback.message.edit_caption(
        caption="🆔 Введи никнейм (логин) мамонта на сайте",
        reply_markup=inline.mammoth_add,
    )
    await state.set_state(MammothEditBalance.login_mammoth_on_site)


@router_callbacks.message(MammothEditBalance.login_mammoth_on_site)
async def get_mammoth_on_site(message: Message, state: FSMContext) -> None:
    await state.update_data(login_mammoth_on_site=message.text)
    login_mammoth_on_site = (await state.get_data())["login_mammoth_on_site"]
    response = requests.post(
        f"{URL}/api/bot/user/{message.from_user.id}",
        json={"login": f"{login_mammoth_on_site}"},
    )
    await message.delete()

    if response.ok:
        await state.clear()
        await MammothEditBalance.message.edit_caption(
            caption="Управление мамонтом 🦣", reply_markup=inline.mammoth_management
        )

    else:
        await MammothEditBalance.message.edit_caption(
            caption=f"{(response.json())}\n🆔 Введи никнейм (логин) мамонта на сайте",
            reply_markup=inline.mammoth_add,
        )


# FAKE DETAILS - brench


@router_callbacks.callback_query(F.data == "fake_details")
async def fake_details(callback: CallbackQuery) -> None:
    fake_details = requests.get(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_fake_details(fake_details),
        reply_markup=inline.fake_details,
        parse_mode=ParseMode.HTML,
    )


@router_callbacks.callback_query(F.data == "fake_details_sber")
async def fake_details_sber(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}", json={"type": "sber"}
    ).json()
    fake_details = requests.get(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_fake_details(fake_details),
        reply_markup=inline.fake_details,
        parse_mode=ParseMode.HTML,
    )


@router_callbacks.callback_query(F.data == "fake_details_tincoff")
async def fake_details_tincoff(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}", json={"type": "tincoff"}
    ).json()
    fake_details = requests.get(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_fake_details(fake_details),
        reply_markup=inline.fake_details,
        parse_mode=ParseMode.HTML,
    )


@router_callbacks.callback_query(F.data == "fake_details_eth")
async def fake_details_eth(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}", json={"type": "eth"}
    ).json()
    fake_details = requests.get(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_fake_details(fake_details),
        reply_markup=inline.fake_details,
        parse_mode=ParseMode.HTML,
    )


@router_callbacks.callback_query(F.data == "fake_details_usdt")
async def fake_details_usdt(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}", json={"type": "usdt"}
    ).json()
    fake_details = requests.get(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_fake_details(fake_details),
        reply_markup=inline.fake_details,
        parse_mode=ParseMode.HTML,
    )


@router_callbacks.callback_query(F.data == "fake_details_btc")
async def fake_details_btc(callback: CallbackQuery) -> None:
    requests.patch(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}", json={"type": "btc"}
    ).json()
    fake_details = requests.get(
        f"{URL}/api/bot/fakerequisite/{callback.from_user.id}"
    ).json()
    await callback.message.edit_caption(
        caption=messages.configure_fake_details(fake_details),
        reply_markup=inline.fake_details,
        parse_mode=ParseMode.HTML,
    )


# SETTING WEBSITE - brench


@router_callbacks.callback_query(F.data == "setting_website")
async def setting_website(callback: CallbackQuery = None) -> None:
    await callback.message.edit_caption(
        caption="Настройка ⚙️",
        reply_markup=inline_builders.get_clava_setting_website(callback.from_user.id),
    )


@router_callbacks.callback_query(F.data == "minimum_deposit")
async def minimum_deposit1(callback: CallbackQuery, state: FSMContext) -> None:
    SettingWebsite.message = callback.message
    await state.set_state(SettingWebsite.min_deposit)
    await callback.message.edit_caption(caption="💰 Введите сумму (не больше 200 000)")


@router_callbacks.message(SettingWebsite.min_deposit)
async def minimum_deposit2(message: Message, state: FSMContext) -> None:
    await message.delete()
    if str(message.text).isnumeric():
        if int(message.text) > 1000:
            if int(message.text) < 200000:
                await state.update_data(min_deposit=message.text)
                requests.post(
                    f"{URL}/api/bot/settingapp/{message.from_user.id}",
                    json={"min_deposit": int((await state.get_data())["min_deposit"])},
                )
                await SettingWebsite.message.edit_caption(
                    caption="Настройка ⚙️",
                    reply_markup=inline_builders.get_clava_setting_website(
                        message.from_user.id
                    ),
                )
                await state.clear()
            else:
                await SettingWebsite.message.edit_caption(
                    caption="❌ Сумма не должна быть больше 200 000 RUB\n\n💰 Введите сумму (не больше 200 000)",
                )
        else:
            await SettingWebsite.message.edit_caption(
                caption="❌ Сумма не должна быть меньше 1 000 RUB\n\n💰 Введите сумму (не больше 200 000)",
            )
    else:
        await SettingWebsite.message.edit_caption(
            caption="❌ Сумма должна быть целым числом\n\n💰 Введите сумму (не больше 200 000)",
        )


@router_callbacks.callback_query(F.data == "min_output")
async def min_output1(callback: CallbackQuery, state: FSMContext) -> None:
    SettingWebsite.message = callback.message
    await state.set_state(SettingWebsite.min_output)
    await callback.message.edit_caption(
        caption="💰 Введите сумму (не больше 1 000 000)"
    )


@router_callbacks.message(SettingWebsite.min_output)
async def min_output2(message: Message, state: FSMContext) -> None:
    await message.delete()
    if str(message.text).isnumeric():
        if int(message.text) > 1:
            if int(message.text) < 1000000:
                await state.update_data(min_output=message.text)
                requests.post(
                    f"{URL}/api/bot/settingapp/{message.from_user.id}",
                    json={"min_output": int((await state.get_data())["min_output"])},
                )
                await SettingWebsite.message.edit_caption(
                    caption="Настройка ⚙️",
                    reply_markup=inline_builders.get_clava_setting_website(
                        message.from_user.id
                    ),
                )
                await state.clear()
            else:
                await SettingWebsite.message.edit_caption(
                    caption="❌ Сумма не должна быть больше 1 000 000 RUB\n\n💰 Введите сумму (не больше 1 000 000)",
                )
        else:
            await SettingWebsite.message.edit_caption(
                caption="❌ Сумма должна быть больше 1 RUB\n\n💰 Введите сумму (не больше 1 000 000)",
            )
    else:
        await SettingWebsite.message.edit_caption(
            caption="❌ Сумма должна быть целым числом\n\n💰 Введите сумму (не больше 1 000 000)",
        )


@router_callbacks.callback_query(F.data == "stop_limit")
async def stop_limit1(callback: CallbackQuery, state: FSMContext) -> None:
    SettingWebsite.message = callback.message
    await state.set_state(SettingWebsite.stop_limit)
    await callback.message.edit_caption(
        caption="💰 Введите сумму (не больше 1 000 000)"
    )


@router_callbacks.message(SettingWebsite.stop_limit)
async def stop_limit2(message: Message, state: FSMContext) -> None:
    await message.delete()
    if str(message.text).isnumeric():
        if int(message.text) > 1:
            if int(message.text) < 1000000:
                await state.update_data(stop_limit=message.text)
                requests.post(
                    f"{URL}/api/bot/settingapp/{message.from_user.id}",
                    json={"stop_limit": int((await state.get_data())["stop_limit"])},
                )
                await SettingWebsite.message.edit_caption(
                    caption="Настройка ⚙️",
                    reply_markup=inline_builders.get_clava_setting_website(
                        message.from_user.id
                    ),
                )
                await state.clear()
            else:
                await SettingWebsite.message.edit_caption(
                    caption="❌ Сумма не должна быть больше 1 000 000 RUB\n\n💰 Введите сумму (не больше 1 000 000)",
                )
        else:
            await SettingWebsite.message.edit_caption(
                caption="❌ Сумма должна быть больше 1 RUB\n\n💰 Введите сумму (не больше 1 000 000)",
            )
    else:
        await SettingWebsite.message.edit_caption(
            caption="❌ Сумма должна быть целым числом\n\n💰 Введите сумму (не больше 1 000 000)",
        )


@router_callbacks.callback_query(F.data == "site_notifications")
async def site_notifications(callback: CallbackQuery) -> None:
    requests.post(
        f"{URL}/api/bot/settingapp/{callback.from_user.id}",
        json={"action": "notifications"},
    )
    await callback.message.edit_caption(
        caption="Настройка ⚙️",
        reply_markup=inline_builders.get_clava_setting_website(
            callback.from_user.id
        ),
    )


@router_callbacks.callback_query(F.data == "site_notifications_bet")
async def site_notifications_bet(callback: CallbackQuery) -> None:
    requests.post(
        f"{URL}/api/bot/settingapp/{callback.from_user.id}",
        json={"action": "notifications_bet"},
    )
    await callback.message.edit_caption(
        caption="Настройка ⚙️",
        reply_markup=inline_builders.get_clava_setting_website(
            callback.from_user.id
        ),
    )


@router_callbacks.callback_query(F.data == "edit_referal_promocode")
async def edit_referal_promocode1(callback: CallbackQuery, state: FSMContext) -> None:
    SettingWebsite.message = callback.message
    await state.set_state(SettingWebsite.referal_promocode)
    await callback.message.edit_caption(
        caption="💰 Введите промокод (не больше 24 символов)"
    )


@router_callbacks.message(SettingWebsite.referal_promocode)
async def edit_referal_promocode2(message: Message, state: FSMContext) -> None:
    await message.delete()
    if len(message.text) <= 24:
        response = requests.patch(
            f"{URL}/api/bot/settingapp/{message.from_user.id}",
            json={"referal_word": message.text},
        )
        if response.ok:
            await SettingWebsite.message.edit_caption(
                caption="Настройка ⚙️",
                reply_markup=inline_builders.get_clava_setting_website(
                    message.from_user.id
                ),
            )
            await state.clear()
        else:
            await SettingWebsite.message.edit_caption(
                caption="❌ Этот промокод уже существует\n\n💰 Введите промокод (не больше 24 символов)",
            )
    else:
        await SettingWebsite.message.edit_caption(
            caption="❌ Промокод не должен быть больше 24 символов\n\n💰 Введите промокод (не больше 24 символов)",
        )


@router_callbacks.callback_query(F.data == "edit_referal_percent")
async def edit_referal_percent1(callback: CallbackQuery, state: FSMContext) -> None:
    SettingWebsite.message = callback.message
    await state.set_state(SettingWebsite.referal_percent)
    await callback.message.edit_caption(caption="💰 Введите процент (не больше 500)")


@router_callbacks.message(SettingWebsite.referal_percent)
async def edit_referal_percent2(message: Message, state: FSMContext) -> None:
    await message.delete()
    if str(message.text).isnumeric():
        if int(message.text) > 0:
            if int(message.text) < 500:
                requests.patch(
                    f"{URL}/api/bot/settingapp/{message.from_user.id}",
                    json={"referal_percent": int(message.text)},
                )
                await SettingWebsite.message.edit_caption(
                    caption="Настройка ⚙️",
                    reply_markup=inline_builders.get_clava_setting_website(
                        message.from_user.id
                    ),
                )
                await state.clear()
            else:
                await SettingWebsite.message.edit_caption(
                    caption="❌ Процент не должен быть больше 500\n\n💰 Введите процент (не больше 500)",
                )
        else:
            await SettingWebsite.message.edit_caption(
                caption="❌ Процент не должен быть меньше 1\n\n💰 Введите процент (не больше 500)",
            )
    else:
        await SettingWebsite.message.edit_caption(
            caption="❌ Процент должен быть целым числом\n\n💰 Введите процент (не больше 500)",
        )


# ---


@router_callbacks.callback_query(F.data == "show_promos")
async def create_promo(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="Ваши промокоды 🎁",
        reply_markup=inline_builders.get_clava_promos(callback.from_user.id),
    )


@router_callbacks.callback_query(F.data.contains("promocode_"))
async def management_user(callback: CallbackQuery) -> None:
    promo_id = str(callback.data).split("_")[-1]
    response = requests.get(f"{URL}/api/bot/promocode/{callback.from_user.id}")
    if response.ok:
        for promo in response.json():
            if int(promo["id"]) == int(promo_id):
                await callback.message.edit_caption(
                    caption=messages.promo_info(promo),
                    reply_markup=inline.back_to_promos,
                    parse_mode=ParseMode.HTML,
                )
    else:
        await callback.answer("Критическая ошибка")


@router_callbacks.callback_query(F.data == "create_promo_choose")
async def create_promo(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="🎁 Выберите тип промокода", reply_markup=inline.create_promo_choose
    )


@router_callbacks.callback_query(F.data == "create_promo_balance")
async def create_promo(callback: CallbackQuery, state: FSMContext) -> None:
    CreatePromo.message = callback.message
    CreatePromo.type = "Баланс"
    await state.set_state(CreatePromo.nominal)
    await callback.message.edit_caption(
        caption="💰 Введите сумму (не больше 1 000 000)"
    )


@router_callbacks.callback_query(F.data == "create_promo_percent")
async def create_promo(callback: CallbackQuery, state: FSMContext) -> None:
    CreatePromo.message = callback.message
    CreatePromo.type = "Бонус к пополнению"
    await state.set_state(CreatePromo.nominal)
    await callback.message.edit_caption(caption="💰 Введите процент (не больше 500)")


@router_callbacks.message(CreatePromo.nominal)
async def create_promo2(message: Message, state: FSMContext) -> None:
    await message.delete()
    if CreatePromo.type == "Баланс":
        if str(message.text).isnumeric():
            if int(message.text) > 0:
                if int(message.text) < 1000000:
                    await state.update_data(nominal=message.text)
                    await state.set_state(CreatePromo.count_activations)
                    await CreatePromo.message.edit_caption(
                        caption="💰 Введите количество активаций (не больше 1 000)"
                    )
                else:
                    await CreatePromo.message.edit_caption(
                        caption="❌ Сумма не должна быть больше 1 000 000 RUB\n\n💰 Введите сумму (не больше 1 000 000)",
                    )
            else:
                await CreatePromo.message.edit_caption(
                    caption="❌ Сумма не должна быть меньше 1 RUB\n\n💰 Введите сумму (не больше 1 000 000)",
                )
        else:
            await CreatePromo.message.edit_caption(
                caption="❌ Сумма должна быть целым числом\n\n💰 Введите сумму (не больше 1 000 000)",
            )
    else:
        if str(message.text).isnumeric():
            if int(message.text) > 0:
                if int(message.text) < 500:
                    await state.update_data(nominal=message.text)
                    await state.set_state(CreatePromo.count_activations)
                    await CreatePromo.message.edit_caption(
                        caption="💰 Введите количество активаций (не больше 1 000)"
                    )
                else:
                    await CreatePromo.message.edit_caption(
                        caption="❌ Процент не должен быть больше 500\n\n💰 Введите процент (не больше 500)",
                    )
            else:
                await CreatePromo.message.edit_caption(
                    caption="❌ Процент не должен быть меньше 1\n\n💰 Введите процент (не больше 500)",
                )
        else:
            await CreatePromo.message.edit_caption(
                caption="❌ Процент должен быть целым числом\n\n💰 Введите процент (не больше 500)",
            )


@router_callbacks.message(CreatePromo.count_activations)
async def create_promo3(message: Message, state: FSMContext) -> None:
    await message.delete()
    if str(message.text).isnumeric():
        if int(message.text) > 0:
            if int(message.text) < 1000:
                await state.update_data(count_activations=message.text)
                await state.set_state(CreatePromo.promo)
                await CreatePromo.message.edit_caption(caption="💰 Введите промокод")
            else:
                await CreatePromo.message.edit_caption(
                    caption="❌ Количество активаций не должно быть больше 1 000\n\n💰 Введите количество активаций (не больше 1 000)",
                )
        else:
            await CreatePromo.message.edit_caption(
                caption="❌ Количество активаций не должно быть меньше 1\n\n💰 Введите количество активаций (не больше 1 000)",
            )
    else:
        await CreatePromo.message.edit_caption(
            caption="❌ Количество активаций должно быть целым числом\n\n💰 Введите количество активаций (не больше 1 000)",
        )


@router_callbacks.message(CreatePromo.promo)
async def create_promo3(message: Message, state: FSMContext) -> None:
    await message.delete()
    await state.update_data(promo=message.text)
    promocode_info = await state.get_data()

    response = requests.post(
        f"{URL}/api/bot/promocode/{message.from_user.id}",
        json={
            "promocode": promocode_info["promo"],
            "type": CreatePromo.type,
            "amount": promocode_info["nominal"],
            "count": promocode_info["count_activations"],
        },
    )
    if response.ok:

        await CreatePromo.message.edit_caption(
            caption=messages.promo_info(
                {
                    "word": promocode_info["promo"],
                    "type": CreatePromo.type,
                    "bonus": promocode_info["nominal"],
                    "count": promocode_info["count_activations"],
                }
            ),
            reply_markup=inline.back_to_promos,
            parse_mode=ParseMode.HTML,
        )

        await state.clear()
    else:
        await CreatePromo.message.edit_caption(
            caption="❌ Такой промокод уже существует\n\n💰 Введите промокод",
        )


#


@router_callbacks.callback_query(F.data == "mega_back")
async def mega_back(callback: CallbackQuery, state: FSMContext) -> None:
    await SettingWebsite.message.edit_caption(
        caption="Настройка ⚙️",
        reply_markup=inline_builders.get_clava_setting_website(),
    )
    await state.clear()


# SETTING BOT - brench


@router_callbacks.callback_query(F.data == "setting_bot")
async def setting_bot(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="Настройка бота 🤖",
        reply_markup=inline_builders.get_clava_setting_bot(callback.from_user.id),
    )


@router_callbacks.callback_query(F.data == "bot_count_signals")
async def bot_count_signals1(callback: CallbackQuery, state: FSMContext) -> None:
    SettingBot.message = callback.message
    await state.set_state(SettingBot.count_signals)
    await callback.message.edit_caption(
        caption="💰 Введите количество сигналов (не больше 100)"
    )


@router_callbacks.message(SettingBot.count_signals)
async def bot_count_signals2(message: Message, state: FSMContext) -> None:
    await message.delete()
    if str(message.text).isnumeric():
        if int(message.text) > 0:
            if int(message.text) < 100:

                requests.post(
                    f"{URL}/api/bot/settingbot/{message.from_user.id}",
                    json={
                        "count_signals": int(message.text),
                    },
                )

                await SettingBot.message.edit_caption(
                    caption="Настройка бота 🤖",
                    reply_markup=inline_builders.get_clava_setting_bot(
                        message.from_user.id
                    ),
                )
                await state.clear()
            else:
                await SettingBot.message.edit_caption(
                    caption="❌ Количество сигналов не должно быть больше 100\n\n💰 Введите количество сигналов (не больше 100)",
                )
        else:
            await SettingBot.message.edit_caption(
                caption="❌ Количество сигналов не должно быть меньше 1\n\n💰 Введите количество сигналов (не больше 100)",
            )
    else:
        await SettingBot.message.edit_caption(
            caption="❌ Количество сигналов должно быть целым числом\n\n💰 Введите количество сигналов (не больше 100)",
        )


@router_callbacks.callback_query(F.data == "delete_bot_support")
async def delete_bot_support(callback: CallbackQuery) -> None:
    requests.delete(
        f"{URL}/api/bot/settingbot/{callback.from_user.id}",
        json={
            "action": "delete_support",
        },
    )
    await callback.answer("Поддержка успешно удалена")
    # await callback.message.edit_caption(
    #     caption="✉️ Напиши сообщение, которое необходимо отправить",
    #     reply_markup=inline.back_to_setting_bot,
    # )


@router_callbacks.callback_query(F.data == "massive_sendler")
async def massive_sendler1(callback: CallbackQuery, state: FSMContext) -> None:
    SettingBot.message = callback.message
    await state.set_state(SettingBot.massive_sendler)
    await callback.message.edit_caption(
        caption="✉️ Напиши сообщение, которое необходимо отправить",
        reply_markup=inline.back_to_setting_bot,
    )


@router_callbacks.message(SettingBot.massive_sendler)
async def massive_sendler2(message: Message, state: FSMContext) -> None:
    await message.delete()
    await state.update_data(massive_sendler=message.text)

    await SettingBot.message.edit_caption(
        caption="Настройка бота 🤖",
        reply_markup=inline_builders.get_clava_setting_bot(message.from_user.id),
    )

    reply_message = (await state.get_data())["massive_sendler"]
    await message.answer(
        text=f"{str(reply_message)}\n\nРассылка сообщеня выше, все верно?",
        reply_markup=inline.back_to_setting_bot_from_masiv_sendler,
    )


@router_callbacks.callback_query(F.data == "start_masiv_sendler")
async def massive_sendler3(callback: CallbackQuery, state: FSMContext) -> None:
    requests.post(
        f"{URL}/api/bot/settingbot/{callback.from_user.id}",
        json={"message_all": (await state.get_data())["massive_sendler"]},
    )
    await state.clear()

    await callback.message.delete()


@router_callbacks.callback_query(F.data == "kill_sendler")
async def kill_sendler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.delete()


@router_callbacks.callback_query(F.data == "bot_uppdate_signals")
async def bot_uppdate_signals(callback: CallbackQuery) -> None:
    requests.post(
        f"{URL}/api/bot/settingbot/{callback.from_user.id}",
        json={"action": "update_signals"},
    )
    await callback.answer("Успешно изменено")


@router_callbacks.callback_query(F.data == "bot_change_support")
async def bot_change_support1(callback: CallbackQuery, state: FSMContext) -> None:
    SettingBot.message = callback.message
    await state.set_state(SettingBot.support_bot)
    await callback.message.edit_caption(
        caption="💰 Введите username в формате (@username или username)",
        reply_markup=inline.back_to_setting_bot,
    )


@router_callbacks.message(SettingBot.support_bot)
async def bot_change_support2(message: Message, state: FSMContext) -> None:
    await message.delete()
    requests.post(
        f"{URL}/api/bot/settingbot/{message.from_user.id}",
        json={"support_bot": message.text},
    )
    await SettingBot.message.edit_caption(
        caption="Настройка бота 🤖",
        reply_markup=inline_builders.get_clava_setting_bot(message.from_user.id),
    )
    await state.clear()


@router_callbacks.callback_query(F.data == "bot_referal_system")
async def bot_referal_system(callback: CallbackQuery) -> None:
    requests.post(
        f"{URL}/api/bot/settingbot/{callback.from_user.id}",
        json={"action": "referal_system"},
    )
    await callback.message.edit_caption(
        caption="Настройка бота 🤖",
        reply_markup=inline_builders.get_clava_setting_bot(callback.from_user.id),
    )


# MIRRORS - branch


@router_callbacks.callback_query(F.data == "mirrors")
async def mirrors(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="Зеркала 🪞", reply_markup=inline.mirrors
    )


@router_callbacks.callback_query(F.data == "add_mirror_bot")
async def add_mirror_bot(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="🪞 Управление зеркалами бота",
        reply_markup=inline_builders.get_clava_add_mirror_bot(callback.from_user.id),
    )


@router_callbacks.callback_query(F.data == "bot_add_processing")
async def bot_add_processing1(callback: CallbackQuery, state: FSMContext) -> None:
    BotAdd.message = callback.message
    await state.set_state(BotAdd.token)
    await callback.message.edit_caption(
        caption="🌐 Введите токен", reply_markup=inline.back_to_add_mirror_bot
    )


@router_callbacks.message(BotAdd.token)
async def bot_add_processing2(message: Message, state: FSMContext) -> None:
    await message.delete()
    response = requests.post(
        f"{URL}/api/bot/mirror/{message.from_user.id}", json={"token": message.text}
    )
    if response.ok:
        await BotAdd.message.edit_caption(
            caption="🪞 Управление зеркалами бота",
            reply_markup=inline_builders.get_clava_add_mirror_bot(message.from_user.id),
        )
        await state.clear()
    else:
        await BotAdd.message.edit_caption(
            caption="❌ Ошибка добавления\n\n🌐 Введите токен",
            reply_markup=inline.back_to_add_mirror_bot,
        )


@router_callbacks.callback_query(F.data.contains("setting_botik_"))
async def management_user(callback: CallbackQuery) -> None:
    token = str(callback.data).split("_")[-1]
    response = requests.get(f"{URL}/api/bot/mirror/{callback.from_user.id}")
    for bot in response.json():
        if bot["token"] == token:
            bot_info = bot
            break

    await callback.message.edit_caption(
        caption=messages.bot_delete(bot_info),
        reply_markup=inline_builders.get_clava_setting_botik(
            callback.from_user.id, bot_info["token"]
        ),
        parse_mode=ParseMode.HTML,
    )


@router_callbacks.callback_query(F.data.contains("delete_botik_"))
async def management_user(callback: CallbackQuery) -> None:
    token = str(callback.data).split("_")[-1]
    requests.delete(
        f"{URL}/api/bot/mirror/{callback.from_user.id}",
        json={"token": token},
    )
    await callback.message.edit_caption(
        caption="🪞 Управление зеркалами бота",
        reply_markup=inline_builders.get_clava_add_mirror_bot(callback.from_user.id),
    )


@router_callbacks.callback_query(F.data == "add_mirror_site")
async def add_mirror_site(callback: CallbackQuery) -> None:
    await callback.message.edit_caption(
        caption="🪞 Управление зеркалами сайта", reply_markup=inline.add_mirror_site
    )


@router_callbacks.callback_query(F.data == "site_add_processing")
async def site_add_processing1(callback: CallbackQuery, state: FSMContext) -> None:
    SiteAdd.message = callback.message
    await state.set_state(SiteAdd.info)
    await callback.message.edit_caption(
        caption="🌐 Введите домен", reply_markup=inline.back_to_add_mirror_site
    )


@router_callbacks.message(SiteAdd.info)
async def site_add_processing2(message: Message, state: FSMContext) -> None:
    await message.delete()

    await SiteAdd.message.edit_caption(
        caption="❌ Ошибка добавления на cloudflare\n\n🌐 Введите домен",
        reply_markup=inline.back_to_add_mirror_site,
    )
    await state.clear()


@router_callbacks.message(SiteAdd.info, F.data == "add_mirror_site")
async def site_add_processing3(message: Message, state: FSMContext) -> None:
    await message.delete()

    await SiteAdd.message.edit_caption(
        caption="🪞 Управление зеркалами сайта", reply_markup=inline.add_mirror_site
    )
    await state.clear()
