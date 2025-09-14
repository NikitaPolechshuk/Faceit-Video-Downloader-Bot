import os

import telebot
from dotenv import load_dotenv

from logger import get_logger

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_SERVER")

logger = get_logger(__name__)


def main():
    try:
        logger.info("----- Проверка .env -----")
        if not BOT_TOKEN:
            raise ValueError("Не найден BOT_TOKEN в переменных окружения!")
        if not API_URL:
            raise ValueError("Не найден API_SERVER в переменных окружения!")

        # Инициализация бота
        bot = telebot.TeleBot(BOT_TOKEN)
        bot.api_server = API_URL
        logger.info("----- Бот запущен -----")

        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}", exc_info=True)
    finally:
        logger.info("----- Бот остановлен -----")


if __name__ == "__main__":
    main()
