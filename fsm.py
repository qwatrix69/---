from aiogram.fsm.state import State, StatesGroup


class ChangeGroupStates(StatesGroup):
    waiting_for_new_group = State()


class AuthStates(StatesGroup):
    waiting_for_group = State()
    waiting_for_admin_confirmation = State()
    waiting_for_new_admin_id = State()


class NotificationStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_text = State()
    waiting_for_deadline = State()


class SubjectNotificationStates(StatesGroup):
    waiting_for_subject = State()


class DeadlineStates(StatesGroup):
    waiting_for_date = State()


class DeletingNotificationStates(StatesGroup):
    waiting_for_notification_id = State()


class EditingNotificationStates(StatesGroup):
    waiting_for_notification_id = State()
    waiting_for_new_subject = State()
    waiting_for_new_text = State()
    waiting_for_new_deadline = State()
