import json
import os

CONFIG_FILE = "config.json"

DEFAULT_SETTINGS = {
    "data_dir": "data",
    "rates_ttl_seconds": 300,
    "base_currency": "USD",
    "log_file": "logs/actions.log",
}


class SettingsLoader:
    """Единая точка конфигурации проекта.

    Singleton через __new__: проще и читабельнее метакласса,
    дополнительные экземпляры при импортах не создаются.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = dict(DEFAULT_SETTINGS)
            cls._instance._load_from_file()
        return cls._instance

    def _load_from_file(self):
        if not os.path.exists(CONFIG_FILE):
            return
        with open(CONFIG_FILE, "r") as f:
            self._settings.update(json.load(f))

    def get(self, key, default=None):
        """Значение настройки по ключу."""
        return self._settings.get(key, default)

    def reload(self):
        """Перечитывает конфигурацию с диска."""
        self._settings = dict(DEFAULT_SETTINGS)
        self._load_from_file()
