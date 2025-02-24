def start_text(admin_info):
    referal_url = admin_info["referal_url"]
    word =admin_info["word"]
    bonus = admin_info["bonus"]
    support = [f"""
👨‍💻 ТП:
└ 👮: {admin_info["support"]}\n""", ""][admin_info["support"] == None]
    
    return f"""🎰 test

🌐 Актуальные домены:
├ https://test.com
├ https://test.com

🤖 Бот для работы:
└ @notFirst_bot

📚 Мануалы:
├ Мануал LuckyJet (https://telegra.ph/Manual-po-LuckyJet-04-24)
├ Материалы LuckyJet (https://t.me/+fuKYxuSnRvs2NDc0)
└ Канал с мануалами (https://t.me/+4Sm7oqAMXn83ODE8)
{support}
🔗 Ваши реферальные ссылки:
└ {referal_url}

🔗 Ваш промокод:
└ {word} + ({bonus}%)
    """


def configure_user_info(user_info):
    return f"""🐘 Мамонт: {user_info["login"]} (<code>{user_info["id"]}</code>)
🧑‍💻 Верификация: {["❌", "✅"][user_info["verification"]]}
🏦 Баланс: {user_info["balance"]} RUB
💸 Метод вывода: {user_info["payout_method_name"]} ({user_info["payout_method_description"]})

📊 Статус ставок: {["❌", "✅"][not user_info["block_bet"]]}
📊 Статус вывода: {["❌", "✅"][not user_info["block_payout"]]}

{["🟢 Онлайн", "🔴 Офлайн"][1]}"""


def configure_fake_details(fake_details):
    return f"""Реквизиты для фейк вывода средств с баланса:
├ Банковская карта (Сбер): <code>{fake_details[0]["card"]}</code>
├ Банковская карта (Тиньк): <code>{fake_details[1]["card"]}</code>
├ Ethereum: <code>{fake_details[2]["card"]}</code>
├ UDST TRC20: <code>{fake_details[3]["card"]}</code>
└ Bitcoin: <code>{fake_details[4]["card"]}</code>"""


def promo_info(promo):
    typ = ["RUB", "%"][promo["type"]!="Баланс"]

    return f"""🎁 Промокод: <code>{promo["word"]}</code>
💳 Тип: {promo["type"]}
💶 Номинал: {promo["bonus"]} {typ}
🌟 Количество активаций: {promo["count"]}"""


def bot_delete(bot_info):
    return f"""👨‍🦰 Username бота: {bot_info["url"]}
🔑 Токен бота: <code>{bot_info["token"]}</code>"""