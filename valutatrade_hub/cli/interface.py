import shlex  # noqa: I001
from datetime import datetime

from valutatrade_hub.core import usecases, utils
from valutatrade_hub.core.currencies import CURRENCIES
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient  # noqa: E501
from valutatrade_hub.parser_service.updater import RatesUpdater


def parse_flags(args):
    """Собирает аргументы вида --ключ значение в словарь."""
    flags = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            flags[args[i]] = args[i + 1]
            i += 2
        else:
            i += 1
    return flags


def fmt_amount(value):
    """Красивое число: крупное с двумя знаками, мелкое с четырьмя."""
    if value >= 1:
        return f"{value:,.2f}"
    return f"{value:.4f}"


def welcome():
    """Печатает приветственный экран со списком команд."""
    print("***Валютный кошелёк***")
    print()
    print("Команды:")
    print("<command> register --username <str> --password <str> - регистрация")
    print("<command> login --username <str> --password <str> - вход")
    print("<command> show-portfolio [--base <str>] - портфель и балансы")
    print("<command> buy --currency <str> --amount <float> - купить валюту")
    print("<command> sell --currency <str> --amount <float> - продать валюту")
    print("<command> get-rate --from <str> --to <str> - курс валюты")
    print("<command> update-rates [--source <str>] - обновить курсы из API")
    print("<command> show-rates [--currency <str>] [--top <int>] [--base <str>] - курсы из кеша")  # noqa: E501
    print("<command> help - справка")
    print("<command> exit - выход")


def need_login(current_user):
    """Проверяет, что пользователь вошёл в систему."""
    if current_user is None:
        print("Сначала выполните login")
        return True
    return False


def run():
    """Главный цикл: читает команду, разбирает флаги, зовёт usecases."""
    welcome()
    current_user = None
    while True:
        try:
            user_input = input("Введите команду: ").strip()
        except EOFError:
            break
        if not user_input:
            continue

        args = shlex.split(user_input)
        cmd = args[0]
        flags = parse_flags(args[1:])

        try:
            match cmd:
                case "register":
                    username = flags.get("--username", "")
                    password = flags.get("--password", "")
                    user = usecases.register(username, password)
                    print(
                        f"Пользователь '{user.username}' зарегистрирован (id={user.user_id}). "  # noqa: E501
                        f"Войдите: login --username {user.username} --password ****"
                    )
                case "login":
                    username = flags.get("--username", "")
                    password = flags.get("--password", "")
                    current_user = usecases.login(username, password)
                    print(f"Вы вошли как '{current_user.username}'")
                case "show-portfolio":
                    if need_login(current_user):
                        continue
                    base = flags.get("--base", "USD").upper()
                    portfolio = usecases.load_portfolio(current_user.user_id)
                    rates = usecases.rates_to_base(base, portfolio.wallets.keys())
                    print(f"Портфель пользователя '{current_user.username}' (база: {base}):")  # noqa: E501
                    for code, wallet in portfolio.wallets.items():
                        cost = wallet.balance * rates[code]
                        print(f"- {code}: {fmt_amount(wallet.balance)}  → {fmt_amount(cost)} {base}")  # noqa: E501
                    total = portfolio.get_total_value(rates, base)
                    print("---------------------------------")
                    print(f"ИТОГО: {fmt_amount(total)} {base}")
                case "buy":
                    if need_login(current_user):
                        continue
                    currency = flags.get("--currency", "").upper()
                    amount = utils.parse_amount(flags.get("--amount", "0"))
                    result = usecases.buy(current_user, currency, amount)
                    print(f"Покупка выполнена: {fmt_amount(amount)} {currency} "
                          f"по курсу {result['rate']:,.2f} USD/{currency}")
                    print("Изменения в портфеле:")
                    print(f"- {currency}: было {fmt_amount(result['before'])} "
                          f"→ стало {fmt_amount(result['after'])}")
                    print(f"Оценочная стоимость покупки: {result['cost']:,.2f} USD")
                case "sell":
                    if need_login(current_user):
                        continue
                    currency = flags.get("--currency", "").upper()
                    amount = utils.parse_amount(flags.get("--amount", "0"))
                    result = usecases.sell(current_user, currency, amount)
                    print(f"Продажа выполнена: {fmt_amount(amount)} {currency} "
                          f"по курсу {result['rate']:,.2f} USD/{currency}")
                    print("Изменения в портфеле:")
                    print(f"- {currency}: было {fmt_amount(result['before'])} "
                          f"→ стало {fmt_amount(result['after'])}")
                    print(f"Оценочная выручка: {result['revenue']:,.2f} USD")
                case "get-rate":
                    currency_from = flags.get("--from", "").upper()
                    currency_to = flags.get("--to", "").upper()
                    rate, updated_at = usecases.get_rate(currency_from, currency_to)
                    updated = datetime.fromisoformat(updated_at).strftime("%Y-%m-%d %H:%M:%S")  # noqa: E501
                    rate_str = f"{rate:,.2f}" if rate >= 1 else f"{rate:.8f}"
                    print(f"Курс {currency_from}→{currency_to}: {rate_str} (обновлено: {updated})")  # noqa: E501
                    back_rate = usecases.get_rate(currency_to, currency_from)[0]
                    print(f"Обратный курс {currency_to}→{currency_from}: {back_rate:,.2f}")  # noqa: E501
                case "update-rates":
                    source = flags.get("--source", "")
                    clients = []
                    if source in ("", "coingecko"):
                        clients.append(CoinGeckoClient())
                    if source in ("", "exchangerate"):
                        clients.append(ExchangeRateApiClient())
                    print("INFO: Starting rates update...")
                    try:
                        total, refreshed = RatesUpdater(clients).run_update()
                        print(f"Update successful. Total rates updated: {total}. "
                              f"Last refresh: {refreshed}")
                    except ApiRequestError as e:
                        print(f"ERROR: Failed to fetch rates: {e}")
                        print("Update completed with errors. Check logs/actions.log for details.")  # noqa: E501
                case "show-rates":
                    snapshot = usecases.db.load(usecases.RATES_FILE, {})
                    pairs = snapshot.get("pairs", {})
                    if not pairs:
                        print("Локальный кеш курсов пуст. Выполните 'update-rates', "
                              "чтобы загрузить данные.")
                        continue
                    base = flags.get("--base", "USD").upper()
                    base_rate = 1.0 if base == "USD" else pairs.get(f"{base}_USD", {}).get("rate")  # noqa: E501
                    if base_rate is None:
                        print(f"Курс для '{base}' не найден в кеше.")
                        continue
                    currency = flags.get("--currency", "").upper()
                    top = flags.get("--top", "")

                    items = sorted(
                        ((pair.split("_")[0], entry["rate"] / base_rate)
                         for pair, entry in pairs.items()),
                        key=lambda item: item[1], reverse=True,
                    )
                    if currency:
                        items = [item for item in items if item[0] == currency]
                        if not items:
                            print(f"Курс для '{currency}' не найден в кеше.")
                            continue
                    if top:
                        items = items[:int(top)]

                    print(f"Rates from cache (updated at {snapshot.get('last_refresh')}):")  # noqa: E501
                    for code, rate in items:
                        rate_str = f"{rate:,.2f}" if rate >= 1 else f"{rate:.5f}"
                        print(f"- {code}_{base}: {rate_str}")
                case "help":
                    welcome()
                case "exit":
                    break
                case _:
                    print(f"Функции {cmd} нет. Попробуйте снова.")
        except InsufficientFundsError as e:
            print(e)
        except CurrencyNotFoundError as e:
            print(e)
            print(f"Поддерживаемые коды: {', '.join(CURRENCIES)}")
        except ApiRequestError as e:
            print(e)
            print("Повторите попытку позже.")
        except ValueError as e:
            print(e)
