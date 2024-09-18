import asyncio
from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.state import StateFilter
from commands import set_commands
from admin import *
import logging


async def register_handlers(dp: Dispatcher):
    dp.message.register(get_start, CommandStart())
    dp.message.register(group_entered, StateFilter(AuthStates.waiting_for_group))
    dp.message.register(admin_confirmation, StateFilter(AuthStates.waiting_for_admin_confirmation))
    dp.message.register(help_list, Command('help'))
    dp.message.register(get_all_notifications, Command('all'))
    dp.message.register(get_subject_notifications, Command('subject'))
    dp.message.register(subject_notifications_entered, StateFilter(SubjectNotificationStates.waiting_for_subject))
    dp.message.register(deadline, Command('deadline'))
    dp.message.register(deadline_entered, StateFilter(DeadlineStates.waiting_for_date))
    dp.message.register(week_notifications, Command('week'))
    dp.message.register(admin_panel, Command('admin'))
    dp.message.register(start_adding_notification, Command('add'))
    dp.message.register(enter_subject, StateFilter(NotificationStates.waiting_for_subject))
    dp.message.register(enter_text, StateFilter(NotificationStates.waiting_for_text))
    dp.message.register(enter_deadline, StateFilter(NotificationStates.waiting_for_deadline))
    dp.message.register(start_deleting_notification, Command('delete'))
    dp.message.register(delete_notification_by_id, StateFilter(DeletingNotificationStates.waiting_for_notification_id))
    dp.message.register(start_editing_notification, Command('edit'))
    dp.message.register(enter_new_subject, StateFilter(EditingNotificationStates.waiting_for_notification_id))
    dp.message.register(enter_new_text, StateFilter(EditingNotificationStates.waiting_for_new_subject))
    dp.message.register(enter_new_deadline, StateFilter(EditingNotificationStates.waiting_for_new_text))
    dp.message.register(finalize_edit_notification, StateFilter(EditingNotificationStates.waiting_for_new_deadline))
    dp.message.register(change_group, Command('change'))
    dp.message.register(new_group_entered, StateFilter(ChangeGroupStates.waiting_for_new_group))
    dp.message.register(get_all_subjects, Command('list'))
    dp.message.register(cancel_command, Command('cancel'))
    dp.message.register(exit_admin_panel, Command('exit'))
    dp.message.register(start_adding_admin, Command('add_admin'))
    dp.message.register(new_admin_entered, StateFilter(AuthStates.waiting_for_new_admin_id))
    dp.message.register(help_list_admin, Command('help_admin'))
    dp.message.register(handle_non_command_message)


async def handle_non_command_message(message: types.Message):
    await message.answer("Я понимаю только команды. Воспользуйтесь /help", reply_markup=reply_keyboard)


async def cancel_command(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer("Операция отменена. Введите следующую команду.", reply_markup=reply_keyboard)


async def start_bot(bot: Bot):
    await set_commands(bot)


async def start_main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=settings.TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    await register_handlers(dp)

    dp.startup.register(start_bot)
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

    scheduler.add_job(send_notifications, 'interval', days=1, kwargs={'bot': bot, 'interval': timedelta(days=3)})
    scheduler.add_job(send_notifications, 'interval', minutes=60, kwargs={'bot': bot, 'interval': timedelta(hours=12)})
    scheduler.start()
    await check_three_days_notifications(bot)

    try:
        users_to_notify = await delete_expired_notifications()
        await send_expired_notifications_notification(users_to_notify)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(start_main())
    except KeyboardInterrupt:
        print('Exit')
