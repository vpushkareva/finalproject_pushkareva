from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Общий интерфейс источника курсов."""

    @abstractmethod
    def fetch_rates(self):
        """Даёт словарь пар вида {"BTC_USD": 59337.21}."""

    def _get(self, url, params=None):
        try:
            response = requests.get(url, params=params, timeout=self.config.request_timeout)  # noqa: E501
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"сетевая ошибка: {e}") from e
        if response.status_code != 200:
            raise ApiRequestError(f"HTTP {response.status_code} от {url}")
        return response.json()


class CoinGeckoClient(BaseApiClient):
    """Курсы криптовалют через CoinGecko, без ключа."""

    source_name = "CoinGecko"

    def __init__(self, config=None):
        self.config = config or ParserConfig()

    def fetch_rates(self):
        ids = ",".join(self.config.crypto_id_map[c] for c in self.config.crypto_currencies)  # noqa: E501
        data = self._get(self.config.coingecko_url, {"ids": ids, "vs_currencies": "usd"})  # noqa: E501

        rates = {}
        for code, coin_id in self.config.crypto_id_map.items():
            if coin_id in data and "usd" in data[coin_id]:
                rates[f"{code}_{self.config.base_currency}"] = data[coin_id]["usd"]
        return rates


class ExchangeRateApiClient(BaseApiClient):
    """Курсы фиатных валют через ExchangeRate-API, ключ из окружения."""

    source_name = "ExchangeRate-API"

    def __init__(self, config=None):
        self.config = config or ParserConfig()

    def fetch_rates(self):
        if not self.config.api_key:
            raise ApiRequestError("не задан ключ EXCHANGERATE_API_KEY")

        url = f"{self.config.exchangerate_url}/{self.config.api_key}/latest/{self.config.base_currency}"  # noqa: E501
        data = self._get(url)

        if data.get("result") != "success":
            raise ApiRequestError(f"неудачный ответ: {data.get('error-type', 'unknown')}")  # noqa: E501

        rates = {}
        for code in self.config.fiat_currencies:
            if code in data.get("rates", {}):
                rates[f"{code}_{self.config.base_currency}"] = 1 / data["rates"][code]
        return rates
