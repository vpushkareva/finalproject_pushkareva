import logging
from datetime import datetime, timezone

from valutatrade_hub.parser_service.storage import RatesStorage


class RatesUpdater:
    """Опрашивает API-клиентов и складывает курсы в хранилище."""

    def __init__(self, clients, storage=None):
        self.clients = clients
        self.storage = storage or RatesStorage()

    def run_update(self):
        """Собирает курсы со всех клиентов, сбой одного не роняет остальных."""
        logger = logging.getLogger("valutatrade")

        all_rates = {}
        sources = {}
        first_error = None
        updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        for client in self.clients:
            name = getattr(client, "source_name", type(client).__name__)
            try:
                rates = client.fetch_rates()
            except Exception as e:
                logger.info("UPDATE client=%s result=ERROR error='%s'", name, e)
                if first_error is None:
                    first_error = e
                continue
            logger.info("UPDATE client=%s result=OK rates=%d", name, len(rates))
            all_rates.update(rates)
            sources.update({pair: name for pair in rates})

        if not all_rates:
            raise first_error

        self.storage.save_snapshot(all_rates, sources, updated_at)
        self.storage.append_history(all_rates, sources, updated_at)
        logger.info("UPDATE result=OK total=%d updated_at=%s", len(all_rates), updated_at)  # noqa: E501
        return len(all_rates), updated_at
