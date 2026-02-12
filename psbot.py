import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta
from threading import Lock

# Инициализация бота с помощью токена
bot = telebot.TeleBot('')

# Пароль для психологов
password_for_psychologists = '123456'

# Инициализация объекта блокировки
lock = Lock()

# Словарь с username'ами психологов и их id
# Для добавления психологов введите имя пользователя из телеграма и айди чата
# Айди чата можно узнать с помощью команды /id
psychologists = {
    'your_username': 33333333
}

# Подключение к базе данных SQLite
conn = sqlite3.connect('psychology_bot.db')
cursor = conn.cursor()

# Создание таблиц в базе данных
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        username TEXT,
        is_psychologist INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        message_text TEXT,
        timestamp DATETIME
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS psychologist_messages (
        id INTEGER PRIMARY KEY,
        psychologist_id INTEGER,
        user_id INTEGER,
        message_text TEXT,
        timestamp DATETIME
    )
''')

conn.commit()

# Переменная для отсеивания обычных пользователей от психологов
is_psychologist = False


# Функция для обработки команды id
@bot.message_handler(commands=['id'])
def get_chat_id(message):
    bot.send_message(message.chat.id, f'ID вашего чата: {message.from_user.id}')


# Функция для обработки команды info
@bot.message_handler(commands=['info'])
def info_about_bot(message):
    bot.send_message(message.chat.id, '''
Этот бот создан для упрощения оказания психологической помощи обучающихся Лицея Финансового Университета, а также педагогического состава.
    ''')


# Функция для обработки команды info
@bot.message_handler(commands=['help'])
def info_about_bot(message):
    bot.send_message(message.chat.id, ''' 
Список доступных команд:

/send_message - Отправить сообщение психологу

/start - Авторизация
/help - Список команд
/info - Информация о боте

Для корректного функционирования бота рекомендуем пользоваться им согласно промежуточным указаниям.
    ''')


# Функция для обработки команды start
@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = types.InlineKeyboardMarkup()
    psychologist_button = types.InlineKeyboardButton('Психолог', callback_data='psychologist')
    user_button = types.InlineKeyboardButton('Пользователь', callback_data='user')
    markup.add(psychologist_button, user_button)
    bot.reply_to(message, '''Добро пожаловать! Прежде чем начать, авторизуйтесь как:''', reply_markup=markup)


# Функция для обработки нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    if call.data == 'psychologist':
        bot.send_message(call.message.chat.id, 'Введите пароль для авторизации как психолога:')
        bot.register_next_step_handler(call.message, process_psychologist_registration_step)
    elif call.data == 'user':
        global is_psychologist
        is_psychologist = False
        bot.send_message(call.message.chat.id, 'Вы успешно авторизованы как пользователь.', reply_markup=types.ReplyKeyboardRemove())
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn1 = types.KeyboardButton(text='Написать сообщение психологу')
        kb.add(btn1)
        bot.send_message(call.message.chat.id, 'Чтобы увидеть список доступных, команд введите /help.', reply_markup=kb)


# Функция для обработки ввода пароля психолога для регистрации
def process_psychologist_registration_step(message):
    if (message.text == password_for_psychologists) and (message.from_user.username in psychologists):
        conn = sqlite3.connect('psychology_bot.db')
        cursor = conn.cursor()

        with lock:
            cursor.execute('INSERT INTO users (user_id, username, is_psychologist) VALUES (?, ?, ?)',
                           (message.from_user.id, message.from_user.username, 1))
            conn.commit()

        global is_psychologist
        is_psychologist = True

        bot.send_message(message.chat.id, 'Вы успешно авторизованы как психолог.')
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
        btn1 = types.KeyboardButton(text='Список команд')
        kb.add(btn1)
        btn2 = types.KeyboardButton(text='Обращения')
        btn3 = types.KeyboardButton(text='Написать ответ')
        kb.add(btn2, btn3)
        btn4 = types.KeyboardButton(text='История ответов')
        kb.add(btn4)
        bot.send_message(message.chat.id, '''
        Список доступных команд для психологов: 

/list_for_ps - Список команд     
/history - История обращений  за последнии 7 дней
/reply - Написать ответ на обращение пользователя
/replies - История ответов на обращения за последние 7 дней
/id - Ваше айди пользователя

Обращаем ваше внимание, что все сообщения хранятся в базе данных не более 7 дней''', reply_markup=kb)  # Здесь перечислить все команды для психологов
    else:
        bot.send_message(message.chat.id, 'Неверный пароль или id чата.', reply_markup=types.ReplyKeyboardRemove())

        is_psychologist = False


# Функция для обработки команды list_for_ps от пользователя
@bot.message_handler(content_types=['text'])
def handle_list_for_ps_command(message):
    global is_psychologist
    if is_psychologist == True:
        if message.text.lower() == '/list_for_ps' or message.text.lower() == 'список команд':
            bot.send_message(message.chat.id, '''
Список доступных команд для психологов: 

/list_for_ps - список команд для психологов        
/history - история обращений  за последние 7 дней
/reply - написать ответ на обращение пользователя
/replies - история ответов на обращения за последнии 7 дней
/id - ваше айди пользователя

Обращаем ваше внимание, что все сообщения хранятся в базе данных не более 7 дней''')
        elif message.text.lower() == '/reply' or message.text.lower() == 'написать ответ':
            bot.send_message(message.chat.id,
                             'Введите айди пользователя, которому хотите ответить (только числа и ничего больше).')
            bot.register_next_step_handler(message, get_reply_user_id)
        elif message.text.lower() == '/history' or message.text.lower() == 'обращения':
            conn = sqlite3.connect('psychology_bot.db')
            cursor = conn.cursor()

            timestamp_threshold = datetime.now() - timedelta(hours=168)

            with lock:
                cursor.execute('SELECT * FROM messages WHERE timestamp > ?', (timestamp_threshold,))
                messages = cursor.fetchall()

            for msg in messages:
                bot.send_message(message.chat.id, f'ID: <u>{msg[1]}</u>: {msg[2]}', parse_mode='HTML')
        elif message.text.lower() == '/replies' or message.text.lower() == 'история ответов':
            conn = sqlite3.connect('psychology_bot.db')
            cursor = conn.cursor()

            timestamp_threshold = datetime.now() - timedelta(hours=168)

            with lock:
                cursor.execute('SELECT * FROM psychologist_messages WHERE timestamp > ?', (timestamp_threshold,))
                messages = cursor.fetchall()

            for msg in messages:
                bot.send_message(message.chat.id, f'Психолог {msg[1]}: {msg[3]}')
    elif is_psychologist == False:
        if message.text.lower() == '/send_message' or message.text.lower() == 'написать сообщение психологу':
            bot.send_message(message.chat.id,'''Введите ваше сообщение и подробно расскажите о совей проблеме. Мы постараемся вам помочь.''')
            bot.send_message(message.chat.id,'''<b><i>Психолог получает ваши сообщения анонимно</i></b> (без указания вашего username, имени и фамилии tg).''',parse_mode='HTML')
            bot.register_next_step_handler(message, process_user_message_step)
        else:
            bot.send_message(message.chat.id, '''Вам недоступна эта команда.
Для её использования авторизуйтесь как психолог.''')


# Функция для обработки команды send_message от пользователя
@bot.message_handler(commands=['send_message'])
def handle_send_message_command(message):
    bot.send_message(message.chat.id, '''Введите ваше сообщение и подробно расскажите о совей проблеме. Мы постараемся вам помочь.''')
    bot.send_message(message.chat.id, '''<b><i>Психолог получает ваши сообщения анонимно</i></b> (без указания вашего username, имени и фамилии tg).''', parse_mode='HTML')
    bot.register_next_step_handler(message, process_user_message_step)


# Функция для обработки сообщения от пользователя
def process_user_message_step(message):
    conn = sqlite3.connect('psychology_bot.db')
    cursor = conn.cursor()

    user_id = message.from_user.id
    message_text = message.text
    timestamp = datetime.now()

    with lock:
        cursor.execute('INSERT INTO messages (user_id, message_text, timestamp) VALUES (?, ?, ?)',
                       (user_id, message_text, timestamp))
        conn.commit()

    bot.send_message(message.chat.id, '''Ваше сообщение отправлено психологу.
Ожидайте, вам скоро ответят.''')
    bot.send_message(message.chat.id, '''Для ввода следующего сообщения необходимо ввести /send_message ещё раз. ''')

# Функция для обработки команды reply для психологов
@bot.message_handler(commands=['reply'])
def handle_reply_command(message):
    global is_psychologist
    if is_psychologist == True:
        bot.send_message(message.chat.id,
                         'Введите айди пользователя, которому хотите ответить (только числа и ничего больше).')
        bot.register_next_step_handler(message, get_reply_user_id)
    else:
        bot.send_message(message.chat.id, '''Вам недоступна эта команда.
Для её использования авторизуйтесь как психолог.''')


def get_reply_user_id(message):
    reply_user_id = message.text
    bot.send_message(message.chat.id, 'Введите текст ответа на обращение.')
    bot.register_next_step_handler(message, lambda msg: get_reply_psychologist_text(msg, reply_user_id))


def get_reply_psychologist_text(message, reply_user_id):
    reply_psychologist_text = message.text
    # Сохранение id пользователя и текста сообщения в базе данных SQLite
    conn = sqlite3.connect('psychology_bot.db')
    cursor = conn.cursor()
    timestamp = datetime.now()
    with lock:
        cursor.execute('INSERT INTO psychologist_messages (user_id, message_text, timestamp) VALUES (?, ?, ?)',
                       (reply_user_id, reply_psychologist_text, timestamp))
        conn.commit()
    bot.send_message(reply_user_id, f'''Ответ психолога:
{reply_psychologist_text}''')


# Функция для обработки команды history от психолога
@bot.message_handler(commands=['history'])
def handle_history_command(message):
    global is_psychologist
    if is_psychologist == True:
        conn = sqlite3.connect('psychology_bot.db')
        cursor = conn.cursor()

        timestamp_threshold = datetime.now() - timedelta(hours=168)

        with lock:
            cursor.execute('SELECT * FROM messages WHERE timestamp > ?', (timestamp_threshold,))
            messages = cursor.fetchall()

        for msg in messages:
            bot.send_message(message.chat.id, f'ID: <u>{msg[1]}</u>: {msg[2]}', parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, '''Вам недоступна эта команда.
Для её использования авторизуйтесь как психолог.''')


# Функция для обработки команды replies от психолога
@bot.message_handler(commands=['replies'])
def handle_replies_command(message):
    global is_psychologist
    if is_psychologist == True:
        conn = sqlite3.connect('psychology_bot.db')
        cursor = conn.cursor()

        timestamp_threshold = datetime.now() - timedelta(hours=168)

        with lock:
            cursor.execute('SELECT * FROM psychologist_messages WHERE timestamp > ?', (timestamp_threshold,))
            messages = cursor.fetchall()

        for msg in messages:
            bot.send_message(message.chat.id, f'Психолог {msg[1]}: {msg[3]}')
    else:
        bot.send_message(message.chat.id, '''Вам недоступна эта команда.
Для её использования авторизуйтесь как психолог.''')


# Обработчик всех остальных сообщений от пользователей и психологов
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.from_user.id not in [psychologist_id for psychologist_id in psychologists.values()]:
        bot.reply_to(message, 'Неправильная команда. Воспользуйтесь /start для начала.')


# Запуск бота
bot.polling()
