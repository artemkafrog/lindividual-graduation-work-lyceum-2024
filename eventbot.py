import telebot
from telebot import types
import sqlite3

# Инициализация бота
bot = telebot.TeleBot('')

# Глобальные переменные для кнопок в командах pnt_add и pnt_presence
last_name_message_text_for_add = ''
last_name_message_text_for_presence = ''

# Глабольная перемнная для сохранения id сообщения в команде pnt_delete
last_message_id_for_delete = 0

participant_states = {}  # колбек участников меропрития
clicked_buttons = set()  # запоминает кнопки нажатые участниками мероприятия

warning_symbols = """".,+-?!*@%^&#=/\:'{}[]""" # опасные символы для навзания мероприятий

# Создание базы данных для участников мероприятия
def create_event_database(event_name):
    conn = sqlite3.connect('event_participants.db')
    cursor = conn.cursor()
    table_name = event_name.replace(" ", "_")  # Заменяем пробелы в имени мероприятия на символ подчеркивания
    cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, name TEXT, presence INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()

# предотвращение ввода команд там, где не следует
def error_prevention(text):
    if text.startswith('/'):
        return False
    else:
        return True

# Обработчик команды start с приветствием и список всех команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, '''Привет! Я бот-помощник для организации мероприятий.
     
Для просмотра всех команд напишите /help.

Настоятельно рекомендую ознакомиться с указаниями по использованию бота /rules.
''')

# Обработчик команды help с выводом всех команд
@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, '''
Список команд:
<b>-------------------------------------</b>
/start - Начать
/help - Список команд
/rules - Указания использования бота
<b>-------------------------------------</b>
/create_event - Создать мероприятие
/pnt_search - Поиск участников
/pnt_list - Список мероприятий
/pnt_add - Добавить участника
/pnt_presence - Список участников (отметить присутствие)
/pnt_delete - Удалить мероприятие
<b>-------------------------------------</b>
/info - Информация о боте
    ''',parse_mode='HTML')

# Обработчик команды rules
@bot.message_handler(commands=['rules'])
def handle_rules(message):
    bot.send_message(message.chat.id, '''
Пользователям рекомендуется прочесть все нижеперечисленные указания.

1. Все команды вводятся через "/".

2. Список всех команд пользователь может посмотреть в сплывающем меню самого бота или при помощи ввода команды /help.

3. После ввода какой-либо команды выводится сообщение с поянениями к следующим шагам.

4. От пользователей требуется внимательное прочтение выводимых пояснений к каждому шагу.

5. НЕ рекомендуется спамить сообщениями и командами. Если бот не ответил на вашу команду, рекомендуем подождать 15 секунд, а после повторить запрос.

Также обращаем ваше внимание, что при одновременном использовании бота большим количеством пользователей, бот может работать с задержками.

''')
# Обработчик команды info для создания мероприятия
@bot.message_handler(commands=['info'])
def handle_info(message):
    bot.send_message(message.chat.id, '''Это бот-помощник для упрощения организации мероприятий.''')

# Обработчик команды create_event для создания мероприятия
@bot.message_handler(commands=['create_event'])
def handle_create_event(message):
    bot.send_message(message.chat.id, '''1. Название мероприятия может содержать <b>только буквы, цифры и пробелы</b>.
    
2. Название мероприятия <b>не должно начинаться с цифры</b>.
    
3. Название мероприятия <b>не должно содержать специальные символы</b>, такие как: запятые, точки, тире и т.п.

4. Название мероприятия <b>не должно быть длиннее 25 символов</b>.
''', parse_mode='HTML')
    bot.send_message(message.chat.id, '''Введите название мероприятия:''')
    bot.register_next_step_handler(message, create_event)

def create_event(message):
    event_name = message.text
    global warning_symbols
    word_tolerance = True
    for i in event_name:
        if i in warning_symbols:
            word_tolerance = False
            break
    if len(event_name) <= 25 and word_tolerance:
        create_event_database(event_name)
        bot.send_message(message.chat.id, f'Мероприятие "{event_name}" создано! Теперь вы можете добавлять участников (/pnt_add).')
    elif len(event_name) <= 25 and word_tolerance == False:
        bot.send_message(message.chat.id, "Ваше название содержит недопустимые символы. Попробуйте другое (/create_event).")
    else:
        bot.send_message(message.chat.id,"Ваше название слишком длинное. Попробуйте другое (/create_event).")


# Обработчик команды pnt_add добавления участников
@bot.message_handler(commands=['pnt_add'])
def handle_presence(message):
    # Логика отображения кнопок с мероприятиями
    conn = sqlite3.connect('event_participants.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    events = cursor.fetchall()
    conn.close()

    keyboard = types.InlineKeyboardMarkup()
    for event in events:
        button = types.InlineKeyboardButton(text=event[0], callback_data=f'add_{event[0]}')
        keyboard.add(button)

    bot.send_message(message.chat.id, "Выберите мероприятие:", reply_markup=keyboard)

# Обработчик нажатий на кнопки с мероприятиями
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def handle_event_selection(call):
    global last_name_message_text_for_add
    event_name = call.data.split('add_')[1]
    last_name_message_text_for_add = event_name
    bot.send_message(call.message.chat.id, f'''Введите список участников или одного участника мероприятия '{event_name}'.
    
Каждый участник должен быть на новой строке. Нумерация строк не обязательна.''')
    bot.register_next_step_handler(call.message, handle_participants_list)

def handle_participants_list(message):
    global last_name_message_text_for_add
    event_name = last_name_message_text_for_add  # Используем сообщение двумя шагами назад
    if error_prevention(message.text):
        participants = [name.strip() for name in message.text.split('\n') if name.strip()]  # Получаем список участников, разделенных символом новой строки
        conn = sqlite3.connect('event_participants.db')
        cursor = conn.cursor()
        for participant in participants:
            cursor.execute(f"INSERT INTO {event_name} (name) VALUES (?)", (participant,))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, "Участник(и) успешно добавлен(ы)!")
    else:
        bot.send_message(message.chat.id, "Ошибка. Попробуйте еще раз.")

# Обработчик команды pnt_list для показа всех мероприятий
@bot.message_handler(commands=['pnt_list'])
def event_list(message):
    conn = sqlite3.connect('event_participants.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    events = cursor.fetchall()
    conn.close()

    keyboard = types.InlineKeyboardMarkup()
    for event in events:
        button = types.InlineKeyboardButton(text=event[0], callback_data=f'presence_{event[0]}')
        keyboard.add(button)

    global last_message_id_for_delete
    last_message_id_for_delete = message.chat.id

    bot.send_message(last_message_id_for_delete, "Список активных мероприятий:", reply_markup=keyboard)


# Обработчик команды pnt_presence присутствия участников на мерориятии
@bot.message_handler(commands=['pnt_presence'])
def handle_presence(message):
    # Логика отображения кнопок с мероприятиями
    conn = sqlite3.connect('event_participants.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    events = cursor.fetchall()
    conn.close()

    keyboard = types.InlineKeyboardMarkup()
    for event in events:
        button = types.InlineKeyboardButton(text=event[0], callback_data=f'presence_{event[0]}')
        keyboard.add(button)

    bot.send_message(message.chat.id, "Выберите мероприятие:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('presence_'))
def handle_event_presence(call):
    # Получаем название мероприятия из call.data
    global last_name_message_text_for_presence
    event_name = call.data.split('presence_')[1]
    last_name_message_text_for_presence = event_name

    # Логика отображения кнопок с участниками мероприятия
    conn = sqlite3.connect('event_participants.db')
    cursor = conn.cursor()

    # Заменяем таблицу наличие таблицы наличие ошибки
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (event_name,))
    exists = cursor.fetchone()
    if exists:
        cursor.execute(f"SELECT * FROM {event_name}")
        participants = cursor.fetchall()

        keyboard = types.InlineKeyboardMarkup()
        for participant in participants:
            button_text = f"{participant[1]} - присутствует" if participant[2] == 1 else participant[1]
            button = types.InlineKeyboardButton(text=button_text, callback_data=f'partisipants_toggle_{participant[0]}_{event_name}')
            keyboard.add(button)

        bot.send_message(call.message.chat.id, f"Список участников мероприятия {event_name}:", reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, f"Мероприятия {event_name} не существует.")

    conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith('partisipants_toggle_'))
def handle_participant_presence_toggle(call):
    data_parts = call.data.split('_')
    participant_id, event_name = data_parts[2], '_'.join(data_parts[3:])

    conn = sqlite3.connect('event_participants.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {event_name}")
    participants = cursor.fetchall()
    keyboard = types.InlineKeyboardMarkup()

    for p in participants:
        name = p[1]

        # Находим участника по ID
        if str(p[0]) == participant_id:
            if name.endswith(' - присутствует'):
                # Убираем " - присутствует" из имени участника
                name = name.replace(' - присутствует', '')

                # Обновляем имя участника в базе данных
                cursor.execute(f"UPDATE {event_name} SET name=? WHERE id=?", (name, participant_id))
            else:
                # Добавляем " - присутствует" к имени участника
                name = f"{name} - присутствует"

                # Обновляем имя участника в базе данных
                cursor.execute(f"UPDATE {event_name} SET name=? WHERE id=?", (name, participant_id))

        # Создаем соответствующие кнопки для участников с обновленным статусом
        status = 'присутствует' if 'присутствует' in name else 'отсутствует'
        button = types.InlineKeyboardButton(text=f"{name}", callback_data=f'partisipants_toggle_{p[0]}_{event_name}')
        keyboard.add(button)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Список участников мероприятия {event_name}:", reply_markup=keyboard)

    conn.commit()
    conn.close()

# обработчик команды pnt_search
@bot.message_handler(commands=['pnt_search'])
def handle_pnt_search(message):
    bot.send_message(message.chat.id, f"Введите имя участника мероприятия:")
    bot.register_next_step_handler(message, search_participant)

def search_participant(message):
    if error_prevention(message.text):
        participant_name = message.text

    # подключаемся ко всем мероприятиям
        conn = sqlite3.connect('event_participants.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        events = cursor.fetchall()
        conn.close()

    # поочереди проверяем каждое мероприятие на наличие участника в нём
        for event in events:
            conn = sqlite3.connect('event_participants.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {event[0]} WHERE name LIKE ?", ('%' + participant_name + '%',))
            results = cursor.fetchall()
            conn.close()

            if results:
                response = f'Результаты поиска в "{event[0]}":\n'
                for result in results:
                    response += f"Полное имя: <b><u>{result[1]}</u></b>\n"
                bot.send_message(message.chat.id, response, parse_mode='HTML')
            else:
                bot.send_message(message.chat.id, f'В "{event[0]}" участник не найден.')
    else:
        bot.send_message(message.chat.id, "Ошибка. Попробуйте еще раз.")

# Обработчик команды pnt_delete для удаления мероприятия
@bot.message_handler(commands=['pnt_delete'])
def handle_delete_event(message):
    conn = sqlite3.connect('event_participants.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    events = cursor.fetchall()
    conn.close()

    keyboard = types.InlineKeyboardMarkup()
    for event in events:
        button = types.InlineKeyboardButton(text=event[0], callback_data=f'delete_{event[0]}')
        keyboard.add(button)

    global last_message_id_for_delete
    last_message_id_for_delete = message.chat.id

    bot.send_message(last_message_id_for_delete, "Выберите мероприятие, которое хотите удалить:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_event_deletion_confirmation(call):
    event_name = call.data.split('delete_')[1]
    keyboard = types.InlineKeyboardMarkup()
    delete_button = types.InlineKeyboardButton(text="Удалить", callback_data=f'confirm_delete_{event_name}')
    cancel_button = types.InlineKeyboardButton(text="Отмена", callback_data=f'cancel_delete_{event_name}')
    keyboard.add(delete_button, cancel_button)
    bot.send_message(call.message.chat.id, f"Вы уверены, что хотите удалить мероприятие '{event_name}'?", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_delete_'))
def handle_confirm_event_deletion(call):
    event_name = call.data.split('confirm_delete_')[1]
    conn = sqlite3.connect('event_participants.db')
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE {event_name}")
    conn.commit()

    bot.send_message(call.message.chat.id, f'''Мероприятие '{event_name}' успешно удалено!
Для просмотра обновленного списка мероприятий введите /pnt_delete.''')
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_delete_'))
def handle_cancel_event_deletion(call):
    event_name = call.data.split('cancel_delete_')[1]
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)  # Удаляем сообщение с кнопками "удалить" и "отмена"
    bot.send_message(call.message.chat.id, f"Удаление мероприятия '{event_name}' отменено.")


# Начало прослушивания сообщений
bot.polling()