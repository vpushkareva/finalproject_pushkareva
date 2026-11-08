from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Базовая валюта: код и имя, общий интерфейс описания."""

    def __init__(self, code, name):
        if not code or not (2 <= len(code) <= 5) or code != code.upper() or " " in code:
            raise ValueError(f"Некорректный код валюты: {code}")
        if not name or not name.strip():
            raise ValueError("Имя валюты не может быть пустым")
        self.code = code
        self.name = name

    @abstractmethod
    def get_display_info(self):
        """Строка описания для UI и логов."""


class FiatCurrency(Currency):
    """Фиатная валюта со страной или зоной эмиссии."""

    def __init__(self, code, name, issuing_country):
        super().__init__(code, name)
        self.issuing_country = issuing_country

    def get_display_info(self):
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта с алгоритмом и капитализацией."""

    def __init__(self, code, name, algorithm, market_cap):
        super().__init__(code, name)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self):
        mcap = f"{self.market_cap:.2e}".replace("e+", "e")
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap})"  # noqa: E501


CURRENCIES = {
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia"),
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 4.1e11),
}


def get_currency(code):
    """Даёт валюту по коду, неизвестный код — CurrencyNotFoundError."""
    currency = CURRENCIES.get(code)
    if currency is None:
        raise CurrencyNotFoundError(code)
    return currency
