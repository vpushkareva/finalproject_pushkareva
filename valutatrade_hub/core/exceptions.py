class ValutaTradeError(Exception):
    """Базовое исключение проекта."""


class InsufficientFundsError(ValutaTradeError):
    """Недостаточно средств на кошельке."""

    def __init__(self, available, required, code):
        super().__init__(
            f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}"  # noqa: E501
        )


class CurrencyNotFoundError(ValutaTradeError):
    """Валюта с таким кодом не поддерживается."""

    def __init__(self, code):
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(ValutaTradeError):
    """Сбой при обращении к внешнему API курсов."""

    def __init__(self, reason):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
