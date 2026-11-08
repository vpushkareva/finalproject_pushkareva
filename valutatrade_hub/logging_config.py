import logging
import os
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader

LOG_FORMAT = "%(levelname)s %(asctime)s %(message)s"
LOG_DATEFMT = "%Y-%m-%dT%H:%M:%S"


def setup_logging():
    """Настраивает лог операций: файл с ротацией, уровень INFO."""
    settings = SettingsLoader()
    log_file = settings.get("log_file", "logs/actions.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("valutatrade")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_file, maxBytes=100_000, backupCount=3, encoding="utf-8")  # noqa: E501
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT))
    logger.addHandler(handler)
    return logger
