from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from database import open_db, close_db
from keyboards import reply_keyboard, reply_keyboard_yes_no
from datetime import datetime, timedelta
from fsm import *
import settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler

ALLOWED_GROUPS = settings.ALLOWED_GROUPS


async def get_start(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    if user_group:
        await message.answer(f'Привет, {message.from_user.first_name}!', reply_markup=reply_keyboard)
        await message.answer(f'Вы уже авторизованы в группе {user_group}', reply_markup=reply_keyboard)
    else:
        await message.answer(f'Привет, {message.from_user.first_name}!', reply_markup=reply_keyboard)
        await message.answer(f'Введите свою группу:')
        await state.set_state(AuthStates.waiting_for_group)
    close_db(conn)


async def group_entered(message: types.Message, state: FSMContext):
    user_group = message.text.strip()
    conn, cursor = open_db()
    if user_group in ALLOWED_GROUPS:
        save_user_group(cursor, conn, message.from_user.id, user_group, message.from_user.first_name)
        await message.answer(f'Вы успешно авторизованы в группе {user_group}', reply_markup=reply_keyboard)

        cursor.execute('SELECT COUNT(*) FROM users WHERE group_name = ? AND is_admin = 1', (user_group,))
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            await message.answer('Ваша группа не имеет администраторов. Хотите стать администратором?', reply_markup=reply_keyboard_yes_no)
            await state.set_state(AuthStates.waiting_for_admin_confirmation)
        else:
            await state.clear()

    else:
        await message.answer('Неправильная группа. Попробуйте еще раз.', reply_markup=reply_keyboard)
    close_db(conn)


async def admin_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        await save_admin_status(message.from_user.id, True)
        await message.answer(f'Вы стали администратором группы!', reply_markup=reply_keyboard)
        await message.answer(f'Используйте команду /admin.', reply_markup=reply_keyboard)
    else:
        await message.answer('Вы отказались от предложения стать администратором.', reply_markup=reply_keyboard)

    await state.clear()


async def change_group(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    if user_group:
        await message.answer(f'Вы в данный момент авторизованы в группе {user_group}. Введите новую группу:')
        await state.set_state(ChangeGroupStates.waiting_for_new_group)
    else:
        await message.answer('Сначала введите свою группу командой /start', reply_markup=reply_keyboard)
    close_db(conn)


async def new_group_entered(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard)
        return

    user_group = message.text.strip()
    conn, cursor = open_db()
    if user_group in ALLOWED_GROUPS:
        save_user_group(cursor, conn, message.from_user.id, user_group, message.from_user.first_name)
        await message.answer(f'Вы успешно авторизованы в группе {user_group}', reply_markup=reply_keyboard)

        cursor.execute('SELECT COUNT(*) FROM users WHERE group_name = ? AND is_admin = 1', (user_group,))
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            await message.answer('Ваша группа не имеет администраторов. Хотите стать администратором?', reply_markup=reply_keyboard_yes_no)
            await state.set_state(AuthStates.waiting_for_admin_confirmation)
        else:
            await state.clear()

    else:
        await message.answer('Неправильная группа. Попробуйте еще раз.', reply_markup=reply_keyboard)
    close_db(conn)


def get_user_group(cursor, user_id):
    cursor.execute('SELECT group_name FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
    return None


def save_user_group(cursor, conn, user_id, group_name, name):
    cursor.execute('INSERT OR REPLACE INTO users (user_id, group_name, name) VALUES (?, ?, ?)', (user_id, group_name, name))
    conn.commit()


async def help_list(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    if user_group:
        await message.answer(f'Список всех команд:\n'
                             f'/start - начало работы\n'
                             f'/change - сменить группу\n'
                             f'/help - список всех команд\n'
                             f'/all - все дедлайны\n'
                             f'/subject - все дедлайны по предмету\n'
                             f'/deadline - все дедлайны до указанной даты\n'
                             f'/week - все дедлайны до конца текущей недели\n'
                             f'/list - список всех предметов\n'
                             f'/cancel - отмена текущей команды', reply_markup=reply_keyboard)
    else:
        await message.answer('Сначала введите свою группу командой /start', reply_markup=reply_keyboard)
    close_db(conn)


async def get_all_notifications(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    if user_group:
        cursor.execute('SELECT id, subject, notification_text, deadline FROM notifications WHERE group_name = ?',
                       (user_group,))
        notifications = cursor.fetchall()
        if notifications:
            response = "Уведомления для вашей группы:\n"
            for notification in notifications:
                response += f"\nID: {notification[0]}\nПредмет: {notification[1]}\nТекст: {notification[2]}\nДедлайн: {notification[3]}\n"
        else:
            response = "У вас нет уведомлений."
        await message.answer(response, reply_markup=reply_keyboard)
    else:
        await message.answer('Сначала введите свою группу командой /start', reply_markup=reply_keyboard)
    close_db(conn)


async def get_subject_notifications(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    if user_group:
        await message.answer('Введите предмет:')
        await state.set_state(SubjectNotificationStates.waiting_for_subject)
    else:
        await message.answer('Сначала введите свою группу командой /start', reply_markup=reply_keyboard)
    close_db(conn)


async def subject_notifications_entered(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard)
        return
    subject = message.text.strip()
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    cursor.execute('SELECT notification_text, deadline FROM notifications WHERE group_name = ? AND subject = ?',
                   (user_group, subject))
    notifications = cursor.fetchall()
    if notifications:
        response = f"Уведомления по предмету {subject}:\n"
        for notification in notifications:
            response += f"\nТекст: {notification[0]}\nДедлайн: {notification[1]}\n"
    else:
        response = f"У вас нет уведомлений по предмету {subject}."
    await message.answer(response, reply_markup=reply_keyboard)
    await state.clear()
    close_db(conn)


async def deadline(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    if user_group:
        await message.answer('Введите конечную дату (в формате YYYY-MM-DD):')
        await state.set_state(DeadlineStates.waiting_for_date)
    else:
        await message.answer('Сначала введите свою группу командой /start', reply_markup=reply_keyboard)
    close_db(conn)


async def deadline_entered(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard)
        return
    try:
        end_date = datetime.strptime(message.text.strip(), '%Y-%m-%d').date()
    except ValueError:
        await message.answer('Неправильный формат даты. Пожалуйста, введите дату в формате YYYY-MM-DD.')
        return

    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    current_date = datetime.now().date()

    cursor.execute('''SELECT subject, notification_text, deadline 
                      FROM notifications 
                      WHERE group_name = ? AND deadline BETWEEN ? AND ?''',
                   (user_group, current_date, end_date))

    notifications = cursor.fetchall()
    if notifications:
        response = f"Уведомления до {end_date}:\n"
        for notification in notifications:
            response += f"\nПредмет: {notification[0]}\nТекст: {notification[1]}\nДедлайн: {notification[2]}\n"
    else:
        response = "У вас нет уведомлений в этом промежутке."

    await message.answer(response, reply_markup=reply_keyboard)
    await state.clear()
    close_db(conn)


async def week_notifications(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    if user_group:
        current_date = datetime.now().date()
        end_of_week = current_date + timedelta(days=(6 - current_date.weekday()))

        cursor.execute('''SELECT subject, notification_text, deadline 
                          FROM notifications 
                          WHERE group_name = ? AND deadline BETWEEN ? AND ?''',
                       (user_group, current_date, end_of_week))

        notifications = cursor.fetchall()
        if notifications:
            response = f"Уведомления до конца недели (до {end_of_week}):\n"
            for notification in notifications:
                response += f"\nПредмет: {notification[0]}\nТекст: {notification[1]}\nДедлайн: {notification[2]}\n"
        else:
            response = "У вас нет уведомлений на этой неделе."
        await message.answer(response, reply_markup=reply_keyboard)
    else:
        await message.answer('Сначала введите свою группу командой /start', reply_markup=reply_keyboard)
    close_db(conn)


async def delete_expired_notifications():
    conn, cursor = open_db()
    current_date = datetime.now().date()

    cursor.execute('''SELECT group_name, subject, notification_text, deadline 
                      FROM notifications 
                      WHERE deadline < ?''', (current_date.strftime('%Y-%m-%d'),))
    deleted_notifications = cursor.fetchall()

    cursor.execute('''DELETE FROM notifications WHERE deadline < ?''', (current_date.strftime('%Y-%m-%d'),))
    conn.commit()
    close_db(conn)

    return deleted_notifications


async def send_expired_notifications_notification(deleted_notifications):
    bot = Bot(token=settings.TOKEN)
    conn, cursor = open_db()

    for notification in deleted_notifications:
        group_name, subject, notification_text, deadline = notification

        cursor.execute('''SELECT user_id FROM users WHERE group_name = ?''', (group_name,))
        users = cursor.fetchall()

        for user in users:
            user_id = user[0]
            await bot.send_message(user_id, f'Уведомление с истекшим дедлайном удалено\n'
                                           f'Предмет: {subject}\n'
                                           f'Текст: {notification_text}\n'
                                           f'Дедлайн: {deadline}')

    close_db(conn)
    await bot.session.close()


async def send_notifications(bot: Bot, interval: timedelta):
    conn, cursor = open_db()
    groups = ALLOWED_GROUPS
    current_date = datetime.now().date()
    current_time = datetime.now().time()

    for group in groups:
        cursor.execute('''SELECT id, subject, notification_text, deadline 
                          FROM notifications 
                          WHERE group_name = ?''', (group,))
        notifications = cursor.fetchall()

        for notification in notifications:
            notification_date = datetime.strptime(notification[3], '%Y-%m-%d').date()
            notification_datetime = datetime.combine(notification_date, datetime.min.time())

            if interval == timedelta(days=3):
                delta = notification_date - current_date
                if delta.days == 3:
                    cursor.execute('SELECT user_id FROM users WHERE group_name = ?', (group,))
                    users = cursor.fetchall()
                    for user in users:
                        user_id = user[0]
                        await bot.send_message(user_id,
                                               f'Дедлайн через три дня!\nПредмет: {notification[1]}\nТекст: {notification[2]}\nДедлайн: {notification[3]}')
            elif interval == timedelta(hours=12):
                delta = notification_datetime - datetime.now()
                if delta <= interval:
                    cursor.execute('SELECT user_id FROM users WHERE group_name = ?', (group,))
                    users = cursor.fetchall()
                    for user in users:
                        user_id = user[0]
                        await bot.send_message(user_id,
                                               f'Дедлайн через 12 часов!\nПредмет: {notification[1]}\nТекст: {notification[2]}\nДедлайн: {notification[3]}')

    close_db(conn)


async def check_three_days_notifications(bot: Bot):
    conn, cursor = open_db()
    current_date = datetime.now().date()
    check_date = current_date + timedelta(days=3)
    cursor.execute('''SELECT id, group_name, subject, notification_text, deadline 
                      FROM notifications
                      WHERE deadline = ?''', (check_date,))
    notifications = cursor.fetchall()
    for notification in notifications:
        cursor.execute('''SELECT user_id FROM users WHERE group_name = ?''', (notification[1],))
        users = cursor.fetchall()
        for user in users:
            user_id = user[0]
            await bot.send_message(user_id, f'Дедлайн через три дня!\n'
                                            f'Предмет: {notification[2]}\n'
                                            f'Текст: {notification[3]}\n'
                                            f'Дедлайн: {notification[4]}')
    close_db(conn)


async def get_all_subjects(message: types.Message):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    cursor.execute('''SELECT DISTINCT subject FROM notifications WHERE group_name = ?''', (user_group,))
    subjects = cursor.fetchall()
    close_db(conn)

    if subjects:
        subjects_list = "\n".join([subject[0] for subject in subjects])
        await message.answer(f"Список всех предметов:\n{subjects_list}", reply_markup=reply_keyboard)
    else:
        await message.answer("Нет доступных предметов.", reply_markup=reply_keyboard)
    close_db(conn)


async def save_admin_status(user_id: int, is_admin: bool):
    conn, cursor = open_db()
    cursor.execute('UPDATE users SET is_admin = ? WHERE user_id = ?', (1 if is_admin else 0, user_id))
    conn.commit()

