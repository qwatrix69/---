from user import *
from aiogram import types
from aiogram.fsm.context import FSMContext
from keyboards import reply_keyboard, reply_keyboard_admin
from datetime import datetime


async def admin_panel(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_info = get_user_group_admin(cursor, message.from_user.id)
    if user_info and user_info['is_admin']:
        await message.answer(f'Добро пожаловать в админ-панель, {message.from_user.first_name}!', reply_markup=reply_keyboard_admin)
    else:
        await message.answer('У вас нет прав доступа к админ-панели.', reply_markup=reply_keyboard)
    close_db(conn)

temp_notification_data = {}


async def start_adding_notification(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_info = get_user_group_admin(cursor, message.from_user.id)
    if user_info and user_info['is_admin']:
        temp_notification_data['group_name'] = user_info['group_name']
        await message.answer('Введите предмет уведомления:')
        await state.set_state(NotificationStates.waiting_for_subject)
    else:
        await message.answer('Вы не имеете прав для выполнения этой команды.', reply_markup=reply_keyboard)
    close_db(conn)


async def enter_subject(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard_admin)
        return
    temp_notification_data['subject'] = message.text.strip()
    await message.answer('Введите текст уведомления:')
    await state.set_state(NotificationStates.waiting_for_text)


async def enter_text(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard_admin)
        return
    temp_notification_data['notification_text'] = message.text.strip()
    await message.answer('Введите дедлайн (в формате YYYY-MM-DD):')
    await state.set_state(NotificationStates.waiting_for_deadline)


async def enter_deadline(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard_admin)
        return
    try:
        deadline_date = datetime.strptime(message.text.strip(), '%Y-%m-%d').date()
    except ValueError:
        await message.answer('Неправильный формат даты. Пожалуйста, введите дату в формате YYYY-MM-DD.')
        return

    temp_notification_data['deadline'] = deadline_date
    conn, cursor = open_db()
    cursor.execute('''INSERT INTO notifications (group_name, subject, notification_text, deadline)
                      VALUES (?, ?, ?, ?)''', (temp_notification_data['group_name'],
                                               temp_notification_data['subject'],
                                               temp_notification_data['notification_text'],
                                               temp_notification_data['deadline'].strftime('%Y-%m-%d')))
    conn.commit()
    close_db(conn)
    await message.answer('Уведомление успешно добавлено!', reply_markup=reply_keyboard_admin)
    await state.clear()


async def start_deleting_notification(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_info = get_user_group_admin(cursor, message.from_user.id)
    if user_info and user_info['is_admin']:
        await get_all_notifications(message, state)
        await message.answer('Введите ID уведомления, которое вы хотите удалить:', reply_markup=reply_keyboard_admin)
        await state.set_state(DeletingNotificationStates.waiting_for_notification_id)
    else:
        await message.answer('У вас нет прав доступа к этой команде.', reply_markup=reply_keyboard)
    close_db(conn)


async def delete_notification_by_id(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard_admin)
        return
    notification_id = message.text.strip()
    conn, cursor = open_db()

    cursor.execute('SELECT * FROM notifications WHERE id = ?', (notification_id,))
    notification = cursor.fetchone()

    if notification:
        cursor.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
        conn.commit()
        await message.answer('Уведомление успешно удалено!', reply_markup=reply_keyboard_admin)
    else:
        await message.answer('Уведомление с таким ID не найдено.', reply_markup=reply_keyboard_admin)

    close_db(conn)
    await state.clear()


async def start_editing_notification(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard_admin)
        return
    conn, cursor = open_db()
    user_info = get_user_group_admin(cursor, message.from_user.id)
    if user_info and user_info['is_admin']:
        await get_all_notifications(message, state)
        await message.answer('Введите ID уведомления, которое вы хотите изменить:', reply_markup=reply_keyboard_admin)
        await state.set_state(EditingNotificationStates.waiting_for_notification_id)
    else:
        await message.answer('У вас нет прав доступа к этой команде.', reply_markup=reply_keyboard)
    close_db(conn)


async def enter_new_subject(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard_admin)
        return
    temp_notification_data['notification_id'] = message.text.strip()
    conn, cursor = open_db()

    cursor.execute('SELECT * FROM notifications WHERE id = ?', (temp_notification_data['notification_id'],))
    notification = cursor.fetchone()

    if notification:
        await message.answer('Введите новый предмет уведомления:')
        await state.set_state(EditingNotificationStates.waiting_for_new_subject)
    else:
        await message.answer('Уведомление с таким ID не найдено.', reply_markup=reply_keyboard_admin)
        await state.clear()

    close_db(conn)


async def enter_new_text(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard_admin)
        return
    temp_notification_data['new_subject'] = message.text.strip()
    await message.answer('Введите новый текст уведомления:')
    await state.set_state(EditingNotificationStates.waiting_for_new_text)


async def enter_new_deadline(message: types.Message, state: FSMContext):
    temp_notification_data['new_text'] = message.text.strip()
    await message.answer('Введите новый дедлайн (в формате YYYY-MM-DD):')
    await state.set_state(EditingNotificationStates.waiting_for_new_deadline)


async def finalize_edit_notification(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("Операция отменена. Введите новую команду.", reply_markup=reply_keyboard_admin)
        return
    try:
        new_deadline_date = datetime.strptime(message.text.strip(), '%Y-%m-%d').date()
    except ValueError:
        await message.answer('Неправильный формат даты. Пожалуйста, введите дату в формате YYYY-MM-DD.')
        return

    temp_notification_data['new_deadline'] = new_deadline_date

    conn, cursor = open_db()
    cursor.execute('''UPDATE notifications 
                      SET subject = ?, notification_text = ?, deadline = ? 
                      WHERE id = ?''', (temp_notification_data['new_subject'],
                                        temp_notification_data['new_text'],
                                        temp_notification_data['new_deadline'],
                                        temp_notification_data['notification_id']))
    conn.commit()
    close_db(conn)
    await message.answer('Уведомление успешно изменено!', reply_markup=reply_keyboard_admin)
    await state.clear()


async def start_adding_admin(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_info = get_user_group_admin(cursor, message.from_user.id)
    if user_info and user_info['is_admin']:
        users = get_users_by_group(cursor, user_info['group_name'])
        user_list = "Список пользователей вашей группы:\n"
        for user_id, name in users:
            user_list += f"Имя: {name}, ID: {user_id}\n"
        await message.answer(user_list)
        await message.answer("Введите ID нового администратора:")
        await state.set_state(AuthStates.waiting_for_new_admin_id)
    else:
        await message.answer("Вы не имеете прав для выполнения этой команды.")
    close_db(conn)


async def new_admin_entered(message: types.Message, state: FSMContext):
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("Некорректный ID. Попробуйте еще раз.")
        return

    conn, cursor = open_db()
    user_info = get_user_group_admin(cursor, message.from_user.id)
    print(user_info)
    if user_info and user_info['is_admin']:
        if get_user_group_admin(cursor, new_admin_id)['group_name'] == user_info['group_name']:
            cursor.execute('''UPDATE users
                              SET is_admin = 1 WHERE user_id = ?''', (new_admin_id,))
            conn.commit()
            await message.answer(f"Пользователь с ID {new_admin_id} добавлен как администратор группы {user_info['group_name']}.")
        else:
            await message.answer("Новый администратор должен быть в той же группе, что и текущий администратор.")
    else:
        await message.answer("Вы не имеете прав для выполнения этой команды.")

    close_db(conn)
    await state.clear()


def get_users_by_group(cursor, group_name):
    cursor.execute('SELECT user_id, name FROM users WHERE group_name = ?', (group_name,))
    return cursor.fetchall()


async def exit_admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Вы вышли из админ-панели.', reply_markup=reply_keyboard)


def get_user_group_admin(cursor, user_id):
    cursor.execute('SELECT group_name, is_admin FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        group_name, is_admin = result
        return {'group_name': group_name, 'is_admin': bool(is_admin)}
    else:
        return None


async def help_list_admin(message: types.Message, state: FSMContext):
    conn, cursor = open_db()
    user_group = get_user_group(cursor, message.from_user.id)
    if user_group:
        await message.answer(f'Список всех команд:\n'
                             f'/help_admin - список команд администратора\n'
                             f'/add - добавить уведомление\n'
                             f'/edit - изменить уведомление\n'
                             f'/delete - удалить уведомление\n'
                             f'/add_admin - добавить администратора\n'
                             f'/exit - выйти из админ-панели\n'
                             f'/cancel - отмена текущей команды', reply_markup=reply_keyboard_admin)
    close_db(conn)