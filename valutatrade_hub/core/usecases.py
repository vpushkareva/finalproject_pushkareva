from datetime import datetime, timedelta

from valutatrade_hub.core import utils
from valutatrade_hub.core.models import Portfolio, User

USERS_FILE = "users.json"
PORTFOLIOS_FILE = "portfolios.json"
RATES_FILE = "rates.json"

DEFAULT_RATES = {
    "USD": 1.0,
    "EUR": 1.0786,
    "BTC": 59337.21,
    "ETH": 3720.00,
    "RUB": 0.01016,
}

RATES_TTL_MINUTES = 5


def register(username, password):
    """Создаёт пользователя и пустой портфель, проверяя уникальность имени."""
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = utils.load_data(USERS_FILE, [])
    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u["user_id"] for u in users), default=0) + 1
    user = User(user_id, username, password)
    users.append(user.to_dict())
    utils.save_data(USERS_FILE, users)

    portfolios = utils.load_data(PORTFOLIOS_FILE, [])
    portfolios.append(Portfolio(user_id).to_dict())
    utils.save_data(PORTFOLIOS_FILE, portfolios)
    return user


def login(username, password):
    """Находит пользователя и проверяет пароль."""
    users = utils.load_data(USERS_FILE, [])
    record = next((u for u in users if u["username"] == username), None)
    if record is None:
        raise ValueError(f"Пользователь '{username}' не найден")

    user = User.from_dict(record)
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")
    return user


def load_portfolio(user_id):
    """Возвращает портфель пользователя."""
    portfolios = utils.load_data(PORTFOLIOS_FILE, [])
    record = next((p for p in portfolios if p["user_id"] == user_id), None)
    if record is None:
        return Portfolio(user_id)
    return Portfolio.from_dict(record)


def save_portfolio(portfolio):
    """Сохраняет портфель, заменяя запись по user_id."""
    portfolios = utils.load_data(PORTFOLIOS_FILE, [])
    for i, p in enumerate(portfolios):
        if p["user_id"] == portfolio.user_id:
            portfolios[i] = portfolio.to_dict()
            break
    else:
        portfolios.append(portfolio.to_dict())
    utils.save_data(PORTFOLIOS_FILE, portfolios)


def get_rate(currency_from, currency_to):
    """Даёт курс пары: свежий из кеша или пересчитывает через USD."""
    if currency_from not in DEFAULT_RATES or currency_to not in DEFAULT_RATES:
        raise ValueError(f"Курс {currency_from}→{currency_to} недоступен. Повторите попытку позже.")  # noqa: E501

    rates = utils.load_data(RATES_FILE, {})
    key = f"{currency_from}_{currency_to}"
    entry = rates.get(key)
    if entry:
        updated = datetime.fromisoformat(entry["updated_at"])
        if datetime.now() - updated < timedelta(minutes=RATES_TTL_MINUTES):
            return entry["rate"], entry["updated_at"]

    rate = DEFAULT_RATES[currency_from] / DEFAULT_RATES[currency_to]
    updated_at = datetime.now().isoformat()
    rates[key] = {"rate": rate, "updated_at": updated_at}
    rates["source"] = "ParserService"
    rates["last_refresh"] = updated_at
    utils.save_data(RATES_FILE, rates)
    return rate, updated_at


def rates_to_base(base_currency):
    """Курсы всех валют к базовой, для оценки портфеля."""
    if base_currency not in DEFAULT_RATES:
        raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")
    return {code: get_rate(code, base_currency)[0] for code in DEFAULT_RATES}


def buy(user, currency_code, amount):
    """Покупает валюту: пополняет кошелёк и возвращает детали сделки."""
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
        "cost": amount * rate,
    }


def sell(user, currency_code, amount):
    """Продаёт валюту: списывает с кошелька и возвращает детали сделки."""
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
        "revenue": amount * rate,
    }
