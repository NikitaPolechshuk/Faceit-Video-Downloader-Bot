import os

import requests
import telebot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в переменных окружения!")

API_URL = os.getenv("API_SERVER")
if not API_URL:
    raise ValueError("Не найден API_SERVER в переменных окружения!")


bot = telebot.TeleBot(BOT_TOKEN)
bot.api_server = API_URL


@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Проверяем какой API фактически используется
    try:
        # Тестовый запрос к нашему API
        response = requests.get(f"{API_URL}/bot{BOT_TOKEN}/getMe", timeout=5)
        if response.status_code == 200:
            bot.reply_to(message, "✅ Работаю через СОБСТВЕННЫЙ API сервер!")
        else:
            bot.reply_to(
                message,
                "⚠️ Использую официальный API (мой сервер недоступен)")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")


if __name__ == "__main__":
    print('Бот запущен, отправье ему сообщение /start для проверки')
    bot.polling()
