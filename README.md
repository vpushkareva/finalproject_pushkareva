# ValutaTrade Hub

Итоговый проект: консольная платформа для отслеживания и симуляции торговли валютами.
Пользователь регистрируется, заводит виртуальный портфель фиатных и крипто-валют,
покупает и продаёт по актуальным курсам, смотрит общий баланс в базовой валюте.

Два сервиса в одном приложении:

- **Core Service** (`valutatrade_hub/core`, `cli`) — пользователи, портфели, сделки, консольный интерфейс;
- **Parser Service** (`valutatrade_hub/parser_service`) — отдельный модуль, который ходит во внешние API
  за курсами и складывает их в локальный кеш.

## Структура

    valutatrade_hub/
    ├── logging_config.py      # лог операций с ротацией (logs/actions.log)
    ├── decorators.py          # @log_action для buy/sell
    ├── core/
    │   ├── currencies.py      # иерархия валют: Currency -> Fiat/Crypto, реестр
    │   ├── exceptions.py      # InsufficientFundsError, CurrencyNotFoundError, ApiRequestError
    │   ├── models.py          # классы User, Wallet, Portfolio
    │   ├── usecases.py        # бизнес-логика: register/login/buy/sell/get_rate
    │   └── utils.py           # валидация сумм, конвертация
    ├── infra/
    │   ├── settings.py        # SettingsLoader (Singleton): пути, TTL, база
    │   └── database.py        # DatabaseManager (Singleton) над JSON-хранилищем
    ├── parser_service/
    │   ├── config.py          # настройки API: ключи, списки валют, таймаут
    │   ├── api_clients.py     # CoinGeckoClient и ExchangeRateApiClient
    │   ├── updater.py         # RatesUpdater: опрос источников, слияние
    │   ├── storage.py         # rates.json (срез) и exchange_rates.json (история)
    │   └── scheduler.py       # обновление по таймеру
    └── cli/
        └── interface.py       # консольные команды

    data/                      # users.json, portfolios.json, rates.json, exchange_rates.json

## Установка и запуск

Нужен [uv](https://docs.astral.sh/uv/).

    uv sync
    uv run valutatrade

или то же самое через точку входа в корне:

    uv run python main.py

## Команды

    register --username alice --password 1234        — регистрация
    login --username alice --password 1234           — вход
    show-portfolio [--base USD]                      — портфель и итоговая стоимость
    buy --currency BTC --amount 0.05                 — купить валюту
    sell --currency BTC --amount 0.01                — продать валюту
    get-rate --from USD --to BTC                     — курс пары
    update-rates [--source coingecko|exchangerate]   — обновить курсы из API
    show-rates [--currency BTC] [--top 3] [--base USD] — курсы из кеша
    help / exit

Строки пишутся в кавычках, суммы — положительные числа, ID генерируется сам.
Пароль не короче 4 символов, хранится как SHA-256 с индивидуальной солью.

## Курсы, кеш и TTL

Parser Service берёт курсы из двух источников:

- **CoinGecko** — криптовалюты (BTC, ETH, SOL), ключ не нужен;
- **ExchangeRate-API** — фиатные (EUR, GBP, RUB), нужен бесплатный ключ.

Ключ не хранится в коде: зарегистрируйтесь на https://www.exchangerate-api.com/
и задайте переменную окружения перед запуском:

    export EXCHANGERATE_API_KEY=ваш_ключ

Core-сервис читает курсы из локального кеша `data/rates.json`. Срок годности кеша
(TTL, по умолчанию 300 секунд) задаётся в настройках SettingsLoader. Устаревший
курс Core обновляет сам, дёргая Parser Service; если источники недоступны —
пользователь получает понятную ошибку. Полная история замеров копится
в `data/exchange_rates.json`, парсер можно крутить и по расписанию
(`parser_service/scheduler.py`).

## Демонстрация

[![asciicast](https://asciinema.org/a/DYHtfCmrhRMQnrcv.svg)](https://asciinema.org/a/DYHtfCmrhRMQnrcv)
