import os
import tempfile
import time

import requests
import telebot
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import constants
from logger import get_logger

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_SERVER")

logger = get_logger(__name__)

logger.info("----- Проверка .env -----")
if not BOT_TOKEN:
    logger.critical(constants.TOKEN_ENV_ERROR)
    raise ValueError(constants.TOKEN_ENV_ERROR)
if not API_URL:
    logger.critical(constants.API_SERVER_ERROR)
    raise ValueError(constants.API_SERVER_ERROR)

# Глобальная переменная для драйвера
driver = None


def setup_bot():
    """Настраивает и возвращает бота"""

    if API_URL:
        telebot.apihelper.API_URL = f"{API_URL}/bot{{0}}/{{1}}"
        telebot.apihelper.FILE_URL = f"{API_URL}/file/bot{{0}}/{{1}}"

        # Проверяем доступность API
        if not check_api_availability():
            logger.critical("Нет подключения к API серверу")
            raise ConnectionError("API сервер недоступен")
        else:
            logger.info("- Используется собственный API сервер -")

    return telebot.TeleBot(BOT_TOKEN)


def check_api_availability():
    """Проверяет доступность API сервера"""
    try:
        response = requests.get(f"{API_URL}/bot{BOT_TOKEN}/getMe", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


# Инициализация бота, перед этим заснем на 10 секунд
# в ожидании загрузки сервера API
time.sleep(5)
bot = setup_bot()


def init_driver():
    """Инициализирует и возвращает Chrome driver"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        # Добавляем опции для обхода защиты
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Автоматически определяем какой браузер использовать
        browser_paths = [
            "/usr/bin/google-chrome-stable",
            "/usr/bin/google-chrome", 
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium"
        ]

        for path in browser_paths:
            if os.path.exists(path):
                chrome_options.binary_location = path
                logger.info(f"Используется браузер: {path}")
                break
        else:
            logger.error("Не найден ни один браузер!")
            return None

        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logger.info("Chrome driver успешно инициализирован")
        return driver

    except Exception as e:
        logger.error(f"Ошибка инициализации Chrome driver: {e}")
        return None


def get_driver():
    """Возвращает драйвер, инициализируя его если нужно"""
    global driver
    if driver is None:
        driver = init_driver()
    return driver


def is_faceit_link(url):
    """Проверяет, является ли текст ссылкой на Faceit видео"""
    # Базовые проверки
    if not url.startswith(('http://', 'https://')):
        return False
    if 'faceit.com' not in url:
        return False
    # Проверяем наличие обязательных сегментов в пути
    if '/players/' not in url or '/videos/' not in url:
        return False
    return True


def get_video_id(url):
    """Быстро извлекает video_id из корректной ссылки Faceit"""
    # Просто разделяем по '/' и берем последний элемент
    return url.split('/')[-1]


def get_mp4_url_from_allstar(video_id):
    """
    Получает прямую ссылку на MP4 видео со страницы allstar.gg
    """
    driver = get_driver()
    if driver is None:
        logger.error("Chrome driver не доступен")
        return None

    try:
        allstar_url = f"https://allstar.gg/iframe?clip={video_id}"
        logger.info(f"Открываем страницу: {allstar_url}")

        # Открываем страницу
        driver.get(allstar_url)

        # Ждем появления видео элементов
        wait = WebDriverWait(driver, 10)
        video_elements = wait.until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "video"))
        )

        # Проверяем все video элементы
        for video in video_elements:
            src = video.get_attribute("src")
            if src and src.endswith('.mp4'):
                logger.info(f"Найдена MP4 ссылка в video tag: {src}")
                return src

        return None
    except Exception as e:
        logger.error(f"Ошибка при получении MP4 ссылки: {str(e)}",
                     exc_info=True)
        return None


def get_title_from_faceit(url):
    driver = get_driver()
    if driver is None:
        logger.error("Chrome driver не доступен")
        return None

    try:
        # Открываем страницу
        logger.info(f"Открываем страницу: {url}")
        driver.get(url)

        # Ждем только загрузки title (быстро)
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete" or d.title
        )

        # Извлекаем заголовок
        title = driver.title
        logger.info(f"Заголовок получен: {title}")
        return title
    except Exception as e:
        logger.error(f"Ошибка при открытие ссылки: {str(e)}",
                     exc_info=True)
        return None


def safe_delete_file(filename):
    """
    Безопасное удаление файла с обработкой ошибок и логированием
    """
    try:
        if filename and os.path.exists(filename):
            os.unlink(filename)
            logger.info(f"Временный файл удален: {filename}")
            return True
    except Exception as e:
        logger.warning(
            f"Не удалось удалить временный файл {filename}: {str(e)}")
    return False


def stream_video_properly(message, mp4_url, faceit_url, title):
    """
    Настоящая потоковая передача с минимальным использованием RAM
    """
    try:
        bot.send_chat_action(message.chat.id, 'upload_video')

        # Создаем временный файл на диске (не в RAM)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_filename = temp_file.name

            # Скачиваем видео прямо в файл с прогрессом
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(mp4_url,
                                    headers=headers,
                                    stream=True,
                                    timeout=60)
            response.raise_for_status()

            # Пишем прямо в файл чанками
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)

            # Закрываем файл перед отправкой
            temp_file.close()

            # Отправляем файл с диска
            with open(temp_filename, 'rb') as video_file:
                bot.send_video(
                    message.chat.id,
                    video_file,
                    caption=f"🎥 <b>{title}</b> 🎮\n <code>{faceit_url}</code>",
                    timeout=120,
                    parse_mode='HTML',
                    supports_streaming=True
                )
            logger.info(f"Видео {mp4_url} отправлено")

        # Удаляем временный файл
        safe_delete_file(temp_filename)

        return True

    except Exception as e:
        logger.error(f"Ошибка при потоковой отправке: {str(e)}")
        # Удаляем временный файл в случае ошибки
        safe_delete_file(temp_filename)
        return False


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     constants.WELCOME_TEXT,
                     parse_mode='Markdown')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработчик текстовых сообщений (ссылок)"""
    try:
        url = message.text.strip()

        # Проверяем, похожа ли строка на ссылку Faceit
        if not is_faceit_link(url):
            bot.send_message(
                message.chat.id,
                constants.NOT_FACEIT_URL_ERROR,
                parse_mode='Markdown'
            )
            return

        # Отправляем сообщение о начале обработки
        processing_msg = bot.send_message(
            message.chat.id,
            constants.START_PROCESS,
            parse_mode='Markdown'
        )
        title = get_title_from_faceit(url)
        video_id = get_video_id(url)
        logger.info(f"Начало обработки видео с id {video_id} "
                    f"от пользователя {message.chat.username}")
        # Получаем MP4 ссылку с allstar.gg
        mp4_url = get_mp4_url_from_allstar(video_id)
        if not mp4_url:
            bot.send_message(
                message.chat.id,
                constants.MP4_NOT_FOUND_ERROR,
                parse_mode='Markdown'
            )
            return
        # Обновляем статус - начинаем отправку
        bot.edit_message_text(
            constants.VIDEO_PROCESS,
            message.chat.id,
            processing_msg.message_id,
            parse_mode='Markdown'
        )

        # Отправка видео
        success = stream_video_properly(message, mp4_url, url, title)

        if success:
            # Удаляем сообщение о обработке
            bot.delete_message(message.chat.id, processing_msg.message_id)
        else:
            bot.edit_message_text(
                constants.DOWNLOAD_ERROR,
                message.chat.id,
                processing_msg.message_id,
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}",
                     exc_info=True)
        bot.send_message(
            message.chat.id,
            constants.PROCESS_ERROR,
            parse_mode='Markdown'
        )


def main():
    try:
        logger.info("----- Бот запущен -----")
        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}", exc_info=True)
    finally:
        logger.info("----- Бот остановлен -----")


if __name__ == "__main__":
    main()
