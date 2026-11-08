import os
from dataclasses import dataclass, field


@dataclass
class ParserConfig:
    """Настройки Parser Service: ключи, эндпоинты, списки валют, пути."""

    api_key: str = field(default_factory=lambda: os.getenv("EXCHANGERATE_API_KEY", ""))

    coingecko_url: str = "https://api.coingecko.com/api/v3/simple/price"
    exchangerate_url: str = "https://v6.exchangerate-api.com/v6"

    base_currency: str = "USD"
    fiat_currencies: tuple = ("EUR", "GBP", "RUB")
    crypto_currencies: tuple = ("BTC", "ETH", "SOL")
    crypto_id_map: dict = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    })

    rates_file: str = "rates.json"
    history_file: str = "exchange_rates.json"

    request_timeout: int = 10
