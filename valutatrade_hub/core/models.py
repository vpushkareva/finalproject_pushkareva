import hashlib
import secrets
from datetime import datetime


class User:
    """Пользователь системы: имя, хеш пароля с солью, дата регистрации."""

    def __init__(self, user_id, username, password):
        self._user_id = user_id
        self._username = username
        self._salt = secrets.token_hex(8)
        self._hashed_password = self._hash(password, self._salt)
        self._registration_date = datetime.now().isoformat()

    def _hash(self, password, salt):
        """Считает sha256 от пароля с солью."""
        return hashlib.sha256((password + salt).encode()).hexdigest()

    @property
    def user_id(self):
        """ID пользователя, только чтение."""
        return self._user_id

    @property
    def username(self):
        """Имя пользователя."""
        return self._username

    @username.setter
    def username(self, new_username):
        """Меняет имя, пустое имя запрещено."""
        if not new_username or not new_username.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = new_username

    def get_user_info(self):
        """Печатает информацию о пользователе без пароля."""
        print(f"Пользователь: {self._username} (id={self._user_id})")
        print(f"Зарегистрирован: {self._registration_date}")

    def change_password(self, new_password):
        """Меняет пароль: новая соль и новый хеш."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._salt = secrets.token_hex(8)
        self._hashed_password = self._hash(new_password, self._salt)

    def verify_password(self, password):
        """Проверяет пароль, сравнивая хеш с сохранённым."""
        return self._hash(password, self._salt) == self._hashed_password

    def to_dict(self):
        """Словарь для сохранения в users.json."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date,
        }

    @classmethod
    def from_dict(cls, data):
        """Собирает пользователя из записи users.json."""
        user = cls(data["user_id"], data["username"], "tmp")
        user._salt = data["salt"]
        user._hashed_password = data["hashed_password"]
        user._registration_date = data["registration_date"]
        return user


class Wallet:
    """Кошелёк одной конкретной валюты."""

    def __init__(self, currency_code, balance=0.0):
        self.currency_code = currency_code
        self._balance = balance

    @property
    def balance(self):
        """Текущий баланс кошелька."""
        return self._balance

    @balance.setter
    def balance(self, value):
        """Меняет баланс: только число и не отрицательное."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount):
        """Пополняет баланс на положительную сумму."""
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        self.balance = self.balance + amount

    def withdraw(self, amount):
        """Снимает средства, если баланс позволяет."""
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        if amount > self._balance:
            raise ValueError("Недостаточно средств")
        self.balance = self.balance - amount

    def get_balance_info(self):
        """Печатает код валюты и баланс."""
        print(f"{self.currency_code}: {self._balance:.4f}")


class Portfolio:
    """Все кошельки одного пользователя."""

    def __init__(self, user_id, wallets=None):
        self._user_id = user_id
        self._wallets = wallets if wallets is not None else {}

    @property
    def user_id(self):
        """ID владельца, только чтение."""
        return self._user_id

    @property
    def wallets(self):
        """Копия словаря кошельков."""
        return dict(self._wallets)

    def add_currency(self, currency_code):
        """Добавляет новый кошелёк, если такого кода ещё нет."""
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк '{currency_code}' уже существует")
        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code):
        """Возвращает кошелёк по коду валюты или None."""
        return self._wallets.get(currency_code)

    def get_total_value(self, rates_to_base, base_currency="USD"):
        """Общая стоимость всех кошельков в базовой валюте."""
        total = 0.0
        for code, wallet in self._wallets.items():
            rate = rates_to_base.get(code)
            if rate is None:
                raise ValueError(f"Не удалось получить курс для {code}→{base_currency}")
            total += wallet.balance * rate
        return total

    def to_dict(self):
        """Словарь для сохранения в portfolios.json."""
        wallets = {code: {"balance": w.balance} for code, w in self._wallets.items()}
        return {"user_id": self._user_id, "wallets": wallets}

    @classmethod
    def from_dict(cls, data):
        """Собирает портфель из записи portfolios.json."""
        wallets = {}
        for code, w in data["wallets"].items():
            wallets[code] = Wallet(code, w["balance"])
        return cls(data["user_id"], wallets)
