import datetime
import os
from dotenv import load_dotenv
from pytz import timezone
import telebot
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
from database.connection import get_connection
from database.users import (
    subscribe_user,
    unsubscribe_user,
    get_subscribed_users,
    is_user_subscribed
)

load_dotenv()

# инициализация бота
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ID беседы группы        ps (замените на реальный ID группового чата, куда нужно слать авто-рассылку)
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')




with get_connection() as conn:
    print("Подключение к PostgreSQL успешно!")

# логика определения четности недели
def get_week_type(target_date=None):
    # определяет в зависимости от номера недели в году
    if target_date is None:
        target_date = datetime.date.today()
    # берем индекс [1] это номер недели в году(+1 в случаи, если неделя определяется наоборот)
    week_number = target_date.isocalendar()[1] + 1

    return 'even' if week_number % 2 == 0 else 'odd'


schedule_data_for_notif = {
    'even': {  # чет неделя
        0: "📅 **Понедельник (Четная неделя):**\n• 9:30 - 11:00: Java (лекция, Гайков А.В., 9 ауд.)\n• 11:30 - 13:00: МП (лекция, Чумаков С.И., 15 ауд.)\n• 14:00 - 15:30: ПиА (практика, Марков А.В.)\n• 16:00 - 17:30: МП (практика, Чумаков С.И., 6 ауд.)",
        1: "📅 **Вторник (Четная неделя):**\n• 9:30 - 11:00: ОХТ (лекция, Александрова Ю.В., 314 ауд.)\n• 11:30 - 13:00: Оформление документов (Юленец Ю.П., 12 ауд.)\n• 14:00 - 15:30: ПиА (лаба, Марков А.В.)\n• 16:00 - 17:30: ПиА (лекция, Марков А.В.)",
        2: "📅 **Среда (Четная неделя):**\n• 9:30 - 11:00: ТАУ (лекция, Душин С.Е., 211 ауд.)\n• 11:30 - 13:00: ВМ (лекция, Гоголь И.В.)\n• 14:00 - 15:30: ОХТ (практика, Александрова Ю.В., 210 ауд.)\n• 16:00 - 17:30: МП (практика, Чумаков С.И., 1 ауд.)",
        3: "📅 **Четверг (Четная неделя):**\n• 9:30 - 11:00: Теорвер (Чумаков С.И., лекция, 15 ауд.)\n• 11:30 - 13:00: ВМ (практика, Гоголь И.В.)\n• 14:00 - 15:30: СА (практика, Чепикова В.Н., 5 ауд.)",
        4: "📅 **Пятница (Четная неделя):**\n• 11:30 - 13:00: Физ-ра\n• 14:00 - 15:30: Java (практика, Гайков А.В., 6 ауд.)\n• 16:00 - 17:30: ТВ (практика, Чумаков С.И., 1 ауд.)",
    },
    'odd': {  # нечет неделя
        0: "📅 **Понедельник (Нечетная неделя):**\n• 9:30 - 11:00: ТАУ (лаба, Гоголь И.В.)\n• 11:30 - 13:00: ТАУ (лаба, Гоголь И.В.)\n• 14:00 - 15:30: СА (лекция, Кулишенко Р.Ю., 15 ауд.)\n• 16:00 - 17:30: МП (практика, Чумаков С.И., 6 ауд.)",
        1: "📅 **Вторник (Нечетная неделя):**\n• 9:30 - 11:00: ОХТ (лекция, Александрова Ю.В., 314 ауд.)\n• 11:30 - 13:00: ВМ (лаба, Гоголь И.В.)\n• 14:00 - 15:30: ВМ (лаба, Гоголь И.В.)\n• 16:00 - 17:30: ПиА (лекция, Марков А.В.)",
        2: "📅 **Среда (Нечетная неделя):**\n• 9:30 - 11:00: ТАУ (лекция, Душин С.Е., 211 ауд.)\n• 11:30 - 13:00: ОХТ (практика, Александрова Ю.В., 210 ауд.)\n• 14:00 - 15:30: Физ-ра",
        3: "📅 **Четверг (Нечетная неделя):**\n• 9:30 - 11:00: ТВ (Чумаков С.И., лекция, 15 ауд.)\n• 11:30 - 13:00: Физ-ра\n• 14:00 - 15:30: СА (практика, Чепикова В.Н., 5 ауд.)",
        4: "📅 **Пятница (Нечетная неделя):**\n• 11:30 - 13:00: ПиА (практика, Марков А.В.)\n• 14:00 - 15:30: Java (практика, Гайков А.В., 6 ауд.)\n• 16:00 - 17:30: ТВ (практика, Чумаков С.И., 1 ауд.)",
    }
}
# тексты расписания
schedule_data = {
    'even': {  # чет неделя
        0: "📅Понедельник (Четная неделя)\n9:30-11:00: Java лекция, Гайков А.В, 9ауд\n11:30-13:00: МП лекция, Чумаков С.И, 15ауд\n14:00-15:30: ПиА практика, Марков А.В\n16:00-17:30: МП практика, Чумаков С.И, 6ауд",
        1: "📅Вторник (Четная неделя)\n9:30-11:00: ОХТ лекция, Александрова Ю.В, 314ауд\n11:30-13:00: Оформление документов Юленец Ю.П, 12ауд\n14:00-15:30: ПиА лаба, Марков А.В\n16:00-17:30: ПиА лекция, Марков А.В",
        2: "📅Среда (Четная неделя)\n9:30-11:00: ТАУ лекция, Душин С.Е, 211ауд\n11:30-13:00: ВМ лекция, Гоголь И.В\n14:00-15:30: ОХТ практика, Александрова Ю.В, 210ауд\n16:00-17:30: МП практика, Чумаков С.И, 1ауд",
        3: "📅Четверг (Четная неделя)\n9:30-11:00: Теорвер Чумаков С.И, лекция, 15ауд\n11:30-13:00: ВМ практика, Гоголь И.В\n14:00-15:30: СА практика, Чепикова В.Н, 5ауд",
        4: "📅Пятница (Четная неделя)\n11:30-13:00: Физра\n14:00-15:30: Java практика, Гайков А.В, 6ауд\n16:00-17:30: ТВ практика, Чумаков С.И, 1ауд",
    },
    'odd': {  # нечетная неделя
        0: "📅Понедельник (Нечетная неделя)\n9:30-11:00: ТАУ лаба, Гоголь И.В\n11:30-13:00: ТАУ лаба, Гоголь И.В\n14:00-15:30: СА лекция, Кулишенко Р.Ю, 15ауд\n16:00-17:30: МП практика, Чумаков С.И, 6ауд",
        1: "📅Вторник (Нечетная неделя)\n9:30-11:00: ОХТ лекция, Александрова Ю.В, 314ауд\n11:30-13:00: ВМ лаба, Гоголь И.В\n14:00-15:30: ВМ лаба, Гоголь И.В\n16:00-17:30: ПиА лекция, Марков А.В",
        2: "📅Среда (Нечетная неделя)\n9:30-11:00: ТАУ лекция, Душин С.Е, 211ауд\n11:30-13:00: ОХТ практика, Александрова Ю.В, 210ауд\n14:00-15:30: Физра",
        3: "📅Четверг (Нечетная неделя)\n9:30-11:00: ТВ лекция, Чумаков С.И, 15ауд\n11:30-13:00: Физра\n14:00-15:30: СА практика, Чепикова В.Н, 5ауд",
        4: "📅Пятница (Нечетная неделя)\n11:30-13:00: ПиА практика, Марков А.В\n14:00-15:30: Java практика, Гайков А.В, 6ауд\n16:00-17:30: ТВ практика, Чумаков С.И, 1ауд",
    }
}


# Функции для чатов и рассылок (длинные)
def get_today_schedule_for_chat():
    today = datetime.date.today()
    week_type = get_week_type(today)
    weekday = today.weekday()
    if weekday > 4:
        return "Сегодня выходной пар нет! 🎉"
    return schedule_data_for_notif[week_type].get(weekday, "На сегодня расписания нет.")


def get_tomorrow_schedule_for_chat():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    week_type = get_week_type(tomorrow)
    weekday = tomorrow.weekday()
    if weekday > 4:
        return "Завтра выходной пар нет! 🎉"
    return schedule_data_for_notif[week_type].get(weekday, "На завтра расписания нет.")


# Функции для всплывающих окон (короткие <200 символов)
def get_today_schedule_for_popup():
    today = datetime.date.today()
    week_type = get_week_type(today)
    weekday = today.weekday()
    if weekday > 4:
        return "Сегодня выходной пар нет! 🎉"
    return schedule_data[week_type].get(weekday, "На сегодня расписания нет.")


def get_tomorrow_schedule_for_popup():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    week_type = get_week_type(tomorrow)
    weekday = tomorrow.weekday()
    if weekday > 4:
        return "Завтра выходной пар нет! 🎉"
    return schedule_data[week_type].get(weekday, "На завтра расписания нет.")


# Функции автоматической рассылки
def morning_group_broadcast():
    text = "🔔 **Пары на сегодня**\n\n" + get_today_schedule_for_chat()
    try:
        bot.send_message(GROUP_CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")


def even_group_broadcast():
    text = "🔔 **Пары на завтра**\n\n" + get_tomorrow_schedule_for_chat()
    try:
        bot.send_message(GROUP_CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")


def morning_personal_reminders():
    text = "⏰ **Утреннее напоминание о парах:**\n\n" + get_today_schedule_for_chat()
    for user_id in get_subscribed_users():
        try:
            bot.send_message(user_id, text, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")


def even_personal_reminders():
    text = "⏰ **Вечернее напоминание о парах:**\n\n" + get_tomorrow_schedule_for_chat()
    for user_id in get_subscribed_users():
        try:
            bot.send_message(user_id, text, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")


# Настройка планировщика
msk_timezone = timezone("Europe/Moscow")
scheduler = BackgroundScheduler(timezone=msk_timezone)

scheduler.add_job(morning_group_broadcast, 'cron', hour=8, minute=55)
scheduler.add_job(morning_personal_reminders, 'cron', hour=8, minute=55)
scheduler.add_job(even_group_broadcast, 'cron', hour=20, minute=0)
scheduler.add_job(even_personal_reminders, 'cron', hour=20, minute=0)
scheduler.start()


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_tomorrow = types.InlineKeyboardButton(text='Расписание на завтра', callback_data='tomorrow')
    btn_today = types.InlineKeyboardButton(text='Расписание на сегодня', callback_data='today')

    # Проверяем, где вызвана команда: в группе/супергруппе или в ЛС
    if message.chat.type in ['group', 'supergroup']:
        # В группе выводим только кнопки расписания
        markup.add(btn_tomorrow, btn_today)
        current_w = "четная" if get_week_type() == 'even' else "нечетная"
        bot.send_message(
            message.chat.id,
            f"Расписание на 3 курс осенний семестр.\nСейчас идет **{current_w} неделя**.",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        # В личных сообщениях выводим полный набор кнопок (включая подписки)
        btn_sub = types.InlineKeyboardButton(text='🔔 Включить напоминания', callback_data='sub_on')
        btn_unsub = types.InlineKeyboardButton(text='🔕 Отключить напоминания', callback_data='sub_off')
        markup.add(btn_tomorrow, btn_today, btn_sub, btn_unsub)

        current_w = "четная" if get_week_type() == 'even' else "нечетная"
        bot.send_message(
            message.chat.id,
            f"Расписание на 3 курс осенний семестр.\nСейчас идет **{current_w} неделя**.",
            reply_markup=markup,
            parse_mode="Markdown"
        )


# Обработчик инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id

    try:
        if call.data == 'tomorrow':
            alert_text = get_tomorrow_schedule_for_popup()
            bot.answer_callback_query(call.id, text=alert_text, show_alert=True)

        elif call.data == 'today':
            alert_text = get_today_schedule_for_popup()
            bot.answer_callback_query(call.id, text=alert_text, show_alert=True)

        elif call.data == 'sub_on':
            if is_user_subscribed(user_id):
                bot.answer_callback_query(
                    call.id,
                    "⚠️ Вы уже подписаны на напоминания!",
                    show_alert=True
                )
            else:
                subscribe_user(user_id)
                bot.send_message(
                    user_id,
                    "✅ Вы успешно подписались на ежедневные напоминания!"
                )
                bot.answer_callback_query(call.id, "Вы успешно подписались!")

        elif call.data == 'sub_off':
            if not is_user_subscribed(user_id):
                bot.answer_callback_query(
                    call.id,
                    "⚠️ Вы и так не подписаны.",
                    show_alert=True
                )
            else:
                unsubscribe_user(user_id)
                bot.send_message(
                    user_id,
                    "❌ Вы отписались от ежедневных напоминаний."
                )
                bot.answer_callback_query(call.id, "Вы отписались!")

    except telebot.apihelper.ApiTelegramException as e:
        # Если пользователь не писал боту в ЛС, Telegram запретит отправку
        if e.error_code == 403:
            bot.answer_callback_query(
                call.id,
                text="⚠️ Напишите боту в личные сообщения /start, чтобы он мог присылать вам ответы!",
                show_alert=True
            )
        else:
            bot.answer_callback_query(call.id, text="Произошла ошибка при отправке.")


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()