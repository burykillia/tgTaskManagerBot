import telebot
from telebot import types
import sqlite3
import datetime

TOKEN = '8755981097:AAHeiGa5zTKirzABO-gMioprwKzbCHHWux4' 
bot = telebot.TeleBot(TOKEN)

# Підключення до бази даних
conn = sqlite3.connect('team_tasks.db', check_same_thread=False)
cur = conn.cursor()

# Створення таблиць
cur.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    assignee TEXT,
    status TEXT DEFAULT 'Pending',
    created TEXT,
    due_date TEXT
)''')
conn.commit()


# Команди

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_mytasks = types.KeyboardButton("📋 Мої завдання")
    btn_alltasks = types.KeyboardButton("📋 Всі завдання")
    btn_stats = types.KeyboardButton("📊 Статистика")
    btn_overdue = types.KeyboardButton("⏰ Прострочені")
    btn_add = types.KeyboardButton("➕ Додати завдання")

    markup.add(btn_mytasks, btn_alltasks)
    markup.add(btn_stats, btn_overdue)
    markup.add(btn_add)

    bot.send_message(message.chat.id, 
        "👋 Вітаю в <b>Team Task Manager</b>!\n\n"
        "Натискай кнопки нижче або використовуй команди 👇",
        parse_mode='HTML',
        reply_markup=markup)

@bot.message_handler(commands=['addtask'])
def add_task(message):
    text = message.text.strip()
    if not text.startswith('/addtask '):
        return

    parts = text.split()[1:]  # все після команди

    if not parts:
        bot.send_message(message.chat.id, 
            "❌ Вкажіть опис завдання.\n"
            "Приклад: /addtask Купити каву @illiaburyk 01.01.2021 14:30")
        return

    due_datetime_str = None
    assignee = None
    description_end = len(parts)

    # Повний формат: DD.MM.YYYY HH:MM 
    if description_end >= 2:
        potential_date = parts[-2]
        potential_time = parts[-1]
        try:
            datetime.datetime.strptime(potential_date + ' ' + potential_time, '%d.%m.%Y %H:%M')
            due_datetime_str = potential_date + ' ' + potential_time
            description_end -= 2
        except ValueError:
            pass

  
    if due_datetime_str is None and description_end >= 1:
        potential_date = parts[-1]
        try:
            datetime.datetime.strptime(potential_date, '%d.%m.%Y')
            due_datetime_str = potential_date + ' 23:59'
            description_end -= 1
        except ValueError:
            pass

    if due_datetime_str is None and description_end >= 1:
        potential_time = parts[-1]
        try:
            t = datetime.datetime.strptime(potential_time, '%H:%M').time()
            today = datetime.date.today()
            due_datetime_str = today.strftime('%d.%m.%Y') + ' ' + potential_time
            description_end -= 1
        except ValueError:
            pass

    # Assignee 
    if description_end >= 1 and parts[description_end - 1].startswith('@'):
        assignee = parts[description_end - 1]
        description_end -= 1

    # Опис
    description = ' '.join(parts[:description_end]).strip()

    if not description:
        bot.send_message(message.chat.id, 
            "❌ Вкажіть опис завдання.\n"
            "Приклад: /addtask Купити каву @illiaburyk 01.01.2021 14:30")
        return

    if assignee is None:
        assignee = "Не вказано"
    if due_datetime_str is None:
        due_datetime_str = "Не вказано"

    created = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')

    cur.execute(
        "INSERT INTO tasks (description, assignee, created, due_date) VALUES (?, ?, ?, ?)",
        (description, assignee, created, due_datetime_str)
    )
    conn.commit()

    bot.send_message(message.chat.id,
        f"✅ Завдання додано!\n"
        f"Опис: {description}\n"
        f"Виконавець: {assignee}\n"
        f"Дедлайн: {due_datetime_str}")

@bot.message_handler(commands=['mytasks'])
def my_tasks(message):
    username = '@' + (message.from_user.username or message.from_user.first_name.lower())
    cur.execute("SELECT id, description, assignee, status, due_date FROM tasks WHERE assignee LIKE ? AND status != 'Done' ORDER BY due_date", 
                (f'%{username}%',))
    tasks = cur.fetchall()
    
    if not tasks:
        bot.send_message(message.chat.id, "У тебе немає активних завдань 🎉")
        return
    
    text = "📋 <b>Мої активні завдання:</b>\n\n"
    for t in tasks:
        text += f"🆔 {t[0]} | {t[1]}\n👤 {t[2]} | 📅 {t[4]} | {t[3]}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    for t in tasks:
        markup.add(types.InlineKeyboardButton(f"✅ Готово (ID {t[0]})", callback_data=f"done_{t[0]}"))
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['alltasks'])
def all_tasks(message):
    cur.execute("SELECT id, description, assignee, status, due_date FROM tasks WHERE status != 'Done' ORDER BY due_date")
    tasks = cur.fetchall()
    
    if not tasks:
        bot.send_message(message.chat.id, "Немає активних завдань у команді 🎉")
        return
    
    text = "📋 <b>Всі активні завдання команди:</b>\n\n"
    for t in tasks:
        text += f"🆔 {t[0]} | {t[1]}\n👤 {t[2]} | 📅 {t[4]} | {t[3]}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    for t in tasks:
        markup.add(types.InlineKeyboardButton(f"✅ Готово (ID {t[0]})", callback_data=f"done_{t[0]}"))
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats(message):
    cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
    data = dict(cur.fetchall())
    total = sum(data.values())
    pending = data.get('Pending', 0)
    done = data.get('Done', 0)
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE due_date < ? AND status != 'Done'", (datetime.date.today().isoformat(),))
    overdue = cur.fetchone()[0]
    
    text = f"""📊 <b>Статистика команди</b>

Загалом завдань: {total}
В роботі: {pending}
Виконано: {done}
Прострочено: {overdue}"""
    
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['overdue'])
def overdue(message):
    now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    cur.execute("""
        SELECT id, description, assignee, due_date 
        FROM tasks 
        WHERE due_date != 'Не вказано' 
          AND due_date < ? 
          AND status != 'Done'
    """, (now,))
    tasks = cur.fetchall()
    
    if not tasks:
        bot.send_message(message.chat.id, "Прострочених завдань немає ✅")
        return
    
    text = "⏰ <b>Прострочені завдання:</b>\n\n"
    for t in tasks:
        text += f"🆔 {t[0]} | {t[1]}\n👤 {t[2]} | 📅 {t[3]}\n\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')

def process_description(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "Додавання скасовано. Натисни кнопку знову.")
        return

    description = message.text.strip()
    if not description:
        msg = bot.send_message(message.chat.id, "❌ Опис не може бути порожнім. Введи опис:")
        bot.register_next_step_handler(msg, process_description)
        return

    # Зберігаємо опис і просимо @тег
    msg = bot.send_message(message.chat.id, 
        f"✅ Опис прийнято: {description}\n\n"
        "👤 Тепер введи @тег виконавця (наприклад @illiaburyk)\n"
        "або напиши 'пропустити':")
    bot.register_next_step_handler(msg, process_assignee, description)

def process_assignee(message, description):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "Додавання скасовано.")
        return

    assignee = message.text.strip()
    if assignee.lower() in ['пропустити', 'skip', 'не вказано']:
        assignee = "Не вказано"
    elif not assignee.startswith('@'):
        assignee = '@' + assignee

    # Автодедлайн — сьогодні 23:59
    due_date = datetime.date.today().strftime('%d.%m.%Y') + ' 23:59'
    created = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')

    cur.execute(
        "INSERT INTO tasks (description, assignee, created, due_date) VALUES (?, ?, ?, ?)",
        (description, assignee, created, due_date)
    )
    conn.commit()

    bot.send_message(message.chat.id,
        f"🎉 Завдання успішно додано!\n\n"
        f"Опис: {description}\n"
        f"Виконавець: {assignee}\n"
        f"Дедлайн: {due_date}\n\n"
        "Натискай кнопки нижче 👇")

    # Показуємо меню знову
    start(message)   # повертає меню

# Обробка кнопок "Готово"
@bot.callback_query_handler(func=lambda call: True)
def callback_done(call):
    if call.data.startswith('done_'):
        task_id = int(call.data.split('_')[1])
        cur.execute("UPDATE tasks SET status = 'Done' WHERE id = ?", (task_id,))
        conn.commit()
        bot.answer_callback_query(call.id, "✅ Завдання позначено виконаним!")
        bot.edit_message_text(
            text=call.message.text.replace('Pending', 'Done').replace('In Progress', 'Done'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

# Запуск бота
print("🤖 Бот запущено...")

@bot.message_handler(func=lambda message: True)
def handle_keyboard(message):
    if not message.text:          # якщо повідомлення без тексту — ігнор
        return
    
    print(f"🔘 Кнопка натиснута: '{message.text}'")   # ← дивись сюди в термінал!

    if message.text == "📋 Мої завдання":
        my_tasks(message)
    elif message.text == "📋 Всі завдання":
        all_tasks(message)
    elif message.text == "📊 Статистика":
        stats(message)
    elif message.text == "⏰ Прострочені":
        overdue(message)
    elif message.text == "➕ Додати завдання":
        msg = bot.send_message(message.chat.id, "✍️ Введи опис завдання:")
        bot.register_next_step_handler(msg, process_description)
    else:
        pass  # ігноруємо все інше



bot.infinity_polling()