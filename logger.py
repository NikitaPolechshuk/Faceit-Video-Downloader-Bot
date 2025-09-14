import logging
import os
from constants import LOG_FILE


def get_logger(name):
    # Настройка расширенного логирования
    # Определяем абсолютный путь к лог-файлу
    script_dir = os.path.dirname(os.path.abspath(__file__))
    _log_file = os.path.join(script_dir, LOG_FILE)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(_log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logging.getLogger(name)
