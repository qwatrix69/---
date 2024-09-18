from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


reply_keyboard = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='/help'),
        KeyboardButton(text='/change'),
        KeyboardButton(text='/all'),
        KeyboardButton(text='/subject')],
    [
        KeyboardButton(text='/list'),
        KeyboardButton(text='/deadline'),
        KeyboardButton(text='/week'),
        KeyboardButton(text='/cancel')
    ],
    [
        KeyboardButton(text='/admin')
    ]
], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выбери команду')

reply_keyboard_admin = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='/add'),
        KeyboardButton(text='/delete'),
        KeyboardButton(text='/edit')],
    [
        KeyboardButton(text='/add_admin'),
        KeyboardButton(text='/help_admin'),
        KeyboardButton(text='/cancel')
    ],
    [
        KeyboardButton(text='/exit'),
    ]
], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выбери команду')

reply_keyboard_yes_no = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='Да'),
        KeyboardButton(text='Нет')
    ]
], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выбери команду')
