import json
import os

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Единая точка доступа к JSON-хранилищу (Singleton через __new__)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = SettingsLoader()
            cls._instance._data_dir = settings.get("data_dir", "data")
        return cls._instance

    def load(self, filename, default):
        """Читает JSON из хранилища, нет файла — возвращает default."""
        try:
            with open(f"{self._data_dir}/{filename}", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return default

    def save(self, filename, data):
        """Записывает JSON в хранилище, создав папку при необходимости."""
        os.makedirs(self._data_dir, exist_ok=True)
        with open(f"{self._data_dir}/{filename}", "w") as f:
            json.dump(data, f, indent=2)
