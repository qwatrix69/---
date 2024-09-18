from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command='start',
            description='Начало работы'
        ),
        BotCommand(
            command='change',
            description='Смена группы'
        ),
        BotCommand(
            command='help',
            description='Список всех команд'
        ),
        BotCommand(
            command='all',
            description='Все уведомления'
        ),
        BotCommand(
            command='subject',
            description='Все уведомления по предмету'
        ),
        BotCommand(
            command='list',
            description='Список всех предметов'
        ),
        BotCommand(
            command='deadline',
            description='Дедлайны до даты'
        ),
        BotCommand(
            command='week',
            description='Дедлайны до конца недели'
        ),
        BotCommand(
            command='cancel',
            description='Отмена текущей команды'
        ),
        BotCommand(
            command='admin',
            description='Панель администратора'
        )
    ]

    await bot.set_my_commands(commands, BotCommandScopeDefault())

