import time

from valutatrade_hub.parser_service.updater import RatesUpdater  # noqa: F401


def run_scheduler(updater, interval_seconds=300):
    """Крутит обновление курсов по таймеру, до Ctrl+C."""
    while True:
        try:
            updater.run_update()
        except Exception as e:
            print(f"Обновление не удалось: {e}")
        time.sleep(interval_seconds)
