import telebot
import config
import logging
from telebot import types
from gpt import ask_gpt
from database import create

bot = telebot.TeleBot(config.BOT_TOKEN)

logging.basicConfigcd(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)

HEROES = ['Человек паук', 'Робин Гуд', 'Флеш', 'Шерлок Холмс']
GENRES = ['Боевик', 'Драма', 'Фантастика', 'Детектив']
SETTINGS = ['Город', 'Лес', 'Космос', 'Пустыня']

user_stories = {}
user_collection = {}


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*HEROES)
    logging.info("Отправка приветственного сообщения")
    bot.send_message(message.chat.id, 'Привет! Я бот-сценарист. Давай напишем вместе историю! Выбери героя:', reply_markup=markup)
    bot.register_next_step_handler(message, choose_hero)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'Я бот сценарист. Давай сделаем сценарий! Напиши /start')
    logging.info("Срабатывание команды /help")


@bot.message_handler(commands=['debug'])
def help(message):
    logging.info(f"Отправка отладочного сообщения пользователю {message.from_user.id}")
    bot.send_message(message.chat.id, 'Отладочная команда!')
    file_path = 'log_file.txt'
    with open(file_path, 'rb') as file:
        bot.send_document(message.chat.id, file)


@bot.message_handler(commands=['finish'])
def finish(message):
    prompt = config.SYSTEM_PROMPT
    prompt += (f"\nНапиши начало истории в стиле {user_stories[message.chat.id]['genre']} "
               f"с главным героем {user_stories[message.chat.id]['hero']}. "
               f"Вот начальный сеттинг: \n{user_stories[message.chat.id]['setting']}. \n"
               "Начало должно быть коротким, 1-3 предложения.\n"
               f"История: {user_stories[message.chat.id]['text']} ")
    collection = [{'role': 'user', 'content': prompt}]
    response = ask_gpt(collection, mode='end')
    user_stories[message.from_user.id]['text'] = user_stories[message.from_user.id]['text'] + ' ' + response
    bot.send_message(message.chat.id, response)
    bot.send_message(message.chat.id, 'Отлично, такая история получилась: ')
    bot.send_message(message.chat.id, user_stories[message.from_user.id]['text'])
    create(user_stories[message.from_user.id]['hero'], user_stories[message.from_user.id]['genre'], user_stories[message.from_user.id]['setting'], user_stories[message.from_user.id]['text'])
    logging.info("Отправка финальной истории")


def choose_hero(message):
    logging.info(f"Пользователь выбрал героя: {message.text}")
    user_stories[message.from_user.id] = {'hero': message.text}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*GENRES)
    bot.send_message(message.chat.id, 'Выбери жанр:', reply_markup=markup)
    bot.register_next_step_handler(message, choose_genre)


def choose_genre(message):
    logging.info(f"Пользователь выбрал жанр: {message.text}")
    user_stories[message.from_user.id]['genre'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*SETTINGS)
    bot.send_message(message.chat.id, 'Выбери сеттинг:', reply_markup=markup)
    bot.register_next_step_handler(message, choose_setting)


def choose_setting(message):
    logging.info(f"Пользователь выбрал сеттинг: {message.text}")
    user_stories[message.from_user.id]['setting'] = message.text
    bot.send_message(message.chat.id, 'Начните историю:')
    bot.register_next_step_handler(message, create_prompt)


def create_prompt(message):
    if not message.text == '/finish':
        logging.info("История в процессе создания")
        try:
            user_stories[message.from_user.id]['text'] = user_stories[message.from_user.id]['text'] + ' ' + message.text
        except KeyError:
            user_stories[message.from_user.id]['text'] = message.text
        prompt = config.SYSTEM_PROMPT
        prompt += (f"\nНапиши начало истории в стиле {user_stories[message.chat.id]['genre']} "
                   f"с главным героем {user_stories[message.chat.id]['hero']}. "
                   f"Вот начальный сеттинг: \n{user_stories[message.chat.id]['setting']}. \n"
                   "Начало должно быть коротким, 1-3 предложения.\n"
                   f"История: {user_stories[message.chat.id]['text']} ")
        collection = [{'role': 'user', 'content': prompt}]
        response = ask_gpt(collection, mode='continue')
        user_stories[message.from_user.id]['text'] = user_stories[message.from_user.id]['text'] + ' ' + response
        bot.send_message(message.chat.id, response)
        dialog(message)
    else:
        finish(message)


def dialog(message):
    logging.info(f"Пользователь продолжает историю: {message.text}")
    bot.send_message(message.chat.id, 'Продолжи историю. Если хочешь ее завершить напиши /finish.')
    bot.register_next_step_handler(message, create_prompt)


if __name__ == '__main__':
    logging.info("Бот запущен")
    bot.polling()