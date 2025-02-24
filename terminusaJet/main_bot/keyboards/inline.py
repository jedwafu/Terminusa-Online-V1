from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


plug = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="ЧО НЕ ОТКРЫВАЕТСЯ ?!!", callback_data="main_menu")]
    ],
)


main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Управление мамонтом 🦣", callback_data="mammoth_management"
            )
        ],
        [InlineKeyboardButton(text="Фейк реквизиты 🪪", callback_data="fake_details")],
        [
            InlineKeyboardButton(
                text="Настройка сайта 🌐", callback_data="setting_website"
            )
        ],
        [InlineKeyboardButton(text="Настройка бота 🤖", callback_data="setting_bot")],
        [InlineKeyboardButton(text="Зеркала 🪞", callback_data="mirrors")],
    ]
)


#


mammoth_management = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Мамонты на сайте 🌐", callback_data="mammoth_on_site"
            ),
            InlineKeyboardButton(
                text="Добавить мамонта ➕", callback_data="mammoth_add"
            ),
        ],
        [InlineKeyboardButton(text="Назад 🔙", callback_data="main_menu")],
    ]
)


mammoth_edit_balance = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Пополнить сумму", callback_data="mammoth_top_up_amount"
            ),
            InlineKeyboardButton(
                text="Снять сумму", callback_data="mammoth_withdraw_amount"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Убрать баланс", callback_data="mammoth_remove_balance"
            )
        ],
        [InlineKeyboardButton(text="Назад 🔙", callback_data="mammoth_management")],
    ]
)


mammoth_add = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад 🔙", callback_data="mammoth_management")],
    ]
)


#


fake_details = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Сменить карту(Сбер)", callback_data="fake_details_sber"
            )
        ],
        [
            InlineKeyboardButton(
                text="Сменить карту(Тиньк)", callback_data="fake_details_tincoff"
            )
        ],
        [
            InlineKeyboardButton(
                text="Сменить Etherium", callback_data="fake_details_eth"
            )
        ],
        [
            InlineKeyboardButton(
                text="Сменить USDT TRC20", callback_data="fake_details_usdt"
            )
        ],
        [
            InlineKeyboardButton(
                text="Сменить Bitcoin", callback_data="fake_details_btc"
            )
        ],
        [InlineKeyboardButton(text="Назад 🔙", callback_data="main_menu")],
    ]
)


#


create_promo_choose = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Баланс", callback_data="create_promo_balance"),
            InlineKeyboardButton(
                text="Бонус к депозиту(%)", callback_data="create_promo_percent"
            ),
        ],
        [
            InlineKeyboardButton(text="Назад 🔙", callback_data="setting_website"),
        ],
    ]
)


#


mirrors = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Бот 🤖", callback_data="add_mirror_bot")],
        [InlineKeyboardButton(text="Сайт 🌐", callback_data="add_mirror_site")],
        [InlineKeyboardButton(text="Назад 🔙", callback_data="main_menu")],
    ]
)


back_to_promos = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад 🔙", callback_data="show_promos")],
    ]
)


back_to_setting_website = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад 🔙", callback_data="mega_back")],
    ]
)

add_mirror_site = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕", callback_data="site_add_processing")],
        [InlineKeyboardButton(text="Назад 🔙", callback_data="mirrors")],
    ]
)


back_to_add_mirror_site = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад 🔙", callback_data="add_mirror_site")],
    ]
)

back_to_add_mirror_bot = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад 🔙", callback_data="add_mirror_bot")],
    ]
)

back_to_setting_bot = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад 🔙", callback_data="setting_bot")],
    ]
)

back_to_setting_bot_from_masiv_sendler = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data="start_masiv_sendler"),
            InlineKeyboardButton(text="Нет", callback_data="kill_sendler"),
        ],
        [InlineKeyboardButton(text="Назад 🔙", callback_data="kill_sendler")],
    ]
)
