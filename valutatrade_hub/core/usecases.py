from datetime import datetime, timedelta, timezone  # noqa: I001

from valutatrade_hub.core.currencies import CURRENCIES, get_currency
from valutatrade_hub.core.exceptions import ApiRequestError, CurrencyNotFoundError
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import convert
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient  # noqa: E501
from valutatrade_hub.parser_service.updater import RatesUpdater

USERS_FILE = "users.json"
PORTFOLIOS_FILE = "portfolios.json"
RATES_FILE = "rates.json"

db = DatabaseManager()
settings = SettingsLoader()


def register(username, password):
    """Создаёт пользователя и пустой портфель, проверяя уникальность имени."""
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = db.load(USERS_FILE, [])
    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u["user_id"] for u in users), default=0) + 1
    user = User(user_id, username, password)
    users.append(user.to_dict())
    db.save(USERS_FILE, users)

    portfolios = db.load(PORTFOLIOS_FILE, [])
    portfolios.append(Portfolio(user_id).to_dict())
    db.save(PORTFOLIOS_FILE, portfolios)
    return user


def login(username, password):
    """Находит пользователя и проверяет пароль."""
    users = db.load(USERS_FILE, [])
    record = next((u for u in users if u["username"] == username), None)
    if record is None:
        raise ValueError(f"Пользователь '{username}' не найден")

    user = User.from_dict(record)
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")
    return user


def load_portfolio(user_id):
    """Возвращает портфель пользователя."""
    portfolios = db.load(PORTFOLIOS_FILE, [])
    record = next((p for p in portfolios if p["user_id"] == user_id), None)
    if record is None:
        return Portfolio(user_id)
    return Portfolio.from_dict(record)


def save_portfolio(portfolio):
    """Сохраняет портфель, заменяя запись по user_id."""
    portfolios = db.load(PORTFOLIOS_FILE, [])
    for i, p in enumerate(portfolios):
        if p["user_id"] == portfolio.user_id:
            portfolios[i] = portfolio.to_dict()
            break
    else:
        portfolios.append(portfolio.to_dict())
    db.save(PORTFOLIOS_FILE, portfolios)


def fetch_rate_from_api(currency_from, currency_to):
    """Обновляет курсы через Parser Service и считает пару через USD."""
    updater = RatesUpdater([CoinGeckoClient(), ExchangeRateApiClient()])
    try:
        updater.run_update()
    except ApiRequestError:
        pass

    snapshot = db.load(RATES_FILE, {})
    pairs = snapshot.get("pairs", {})

    def to_usd(code):
        if code == "USD":
            return 1.0
        entry = pairs.get(f"{code}_USD")
        if entry is None:
            raise ApiRequestError(f"нет данных по паре {code}_USD")
        return entry["rate"]

    return to_usd(currency_from) / to_usd(currency_to)


def get_rate(currency_from, currency_to):
    """Даёт курс пары: свежий из кеша или после обновления парсером."""
    get_currency(currency_from)
    get_currency(currency_to)

    key = f"{currency_from}_{currency_to}"
    ttl = timedelta(seconds=settings.get("rates_ttl_seconds", 300))

    snapshot = db.load(RATES_FILE, {})
    entry = snapshot.get("pairs", {}).get(key)
    if entry:
        updated = datetime.fromisoformat(entry["updated_at"])
        if datetime.now(timezone.utc) - updated < ttl:
            return entry["rate"], entry["updated_at"]

    rate = fetch_rate_from_api(currency_from, currency_to)
    return rate, snapshot.get("last_refresh", datetime.now(timezone.utc).isoformat())


def rates_to_base(base_currency):
    """Курсы всех валют к базовой, для оценки портфеля."""
    try:
        get_currency(base_currency)
    except CurrencyNotFoundError:
        raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")
    return {code: get_rate(code, base_currency)[0] for code in CURRENCIES}


@log_action("BUY", verbose=True)
def buy(user, currency_code, amount):
    """Покупает валюту: пополняет кошелёк и возвращает детали сделки."""
    get_currency(currency_code)
    portfolio = load_portfolio(user.user_id)
    if portfolio.get_wallet(currency_code) is None:
        portfolio.add_currency(currency_code)
    wallet = portfolio.get_wallet(currency_code)

    rate, _ = get_rate(currency_code, "USD")
    before = wallet.balance
    wallet.deposit(amount)
    save_portfolio(portfolio)
    return {
        "rate": rate,
        "before": before,
        "after": wallet.balance,
        "cost": convert(amount, rate),
    }


@log_action("SELL", verbose=True)
def sell(user, currency_code, amount):
    """Продаёт валюту: списывает с кошелька и возвращает детали сделки."""
    get_currency(currency_code)
    portfolio = load_portfolio(user.user_id)
    wallet = portfolio.get_wallet(currency_code)
    if wallet is None:
        raise ValueError(
            f"У вас нет кошелька '{currency_code}'. "
            "Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    rate, _ = get_rate(currency_code, "USD")
    before = wallet.balance
    wallet.withdraw(amount)
    save_portfolio(portfolio)
    return {
        "rate": rate,
        "before": before,
        "after": wallet.balance,
        "revenue": convert(amount, rate),
    }
