import json
import os

from valutatrade_hub.infra.settings import SettingsLoader


class RatesStorage:
    """Читает и пишет rates.json (срез) и exchange_rates.json (история)."""

    def __init__(self):
        settings = SettingsLoader()
        self.data_dir = settings.get("data_dir", "data")

    def _path(self, filename):
        return os.path.join(self.data_dir, filename)

    def load_snapshot(self):
        """Читает текущий срез курсов, нет файла — пустые пары."""
        try:
            with open(self._path("rates.json"), "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"pairs": {}}

    def load_history(self):
        """Читает журнал измерений, нет файла — пустой список."""
        try:
            with open(self._path("exchange_rates.json"), "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _write_atomic(self, filename, data):
        os.makedirs(self.data_dir, exist_ok=True)
        tmp = self._path(f"{filename}.tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self._path(filename))

    def save_snapshot(self, rates, sources, updated_at):
        """Пишет срез: новая пара побеждает, только если она свежее."""
        snapshot = self.load_snapshot()
        pairs = snapshot.get("pairs", {})
        for pair, rate in rates.items():
            pairs[pair] = {"rate": rate, "updated_at": updated_at, "source": sources[pair]}  # noqa: E501
        self._write_atomic("rates.json", {"pairs": pairs, "last_refresh": updated_at})

    def append_history(self, rates, sources, updated_at):
        """Добавляет замеры в журнал, дубликаты по id не пишет."""
        history = self.load_history()
        known_ids = {entry["id"] for entry in history}

        for pair, rate in rates.items():
            entry_id = f"{pair}_{updated_at}"
            if entry_id in known_ids:
                continue
            from_currency, to_currency = pair.split("_")
            history.append({
                "id": entry_id,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "timestamp": updated_at,
                "source": sources[pair],
                "meta": {},
            })
        self._write_atomic("exchange_rates.json", history)
