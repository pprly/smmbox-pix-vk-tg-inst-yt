from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_title_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для подтверждения названия видео
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, всё верно", callback_data="title_confirm"),
            InlineKeyboardButton(text="❌ Изменить", callback_data="title_edit")
        ]
    ])
    return keyboard


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой отмены
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ])
    return keyboard
