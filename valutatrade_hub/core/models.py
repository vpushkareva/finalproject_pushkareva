import hashlib
import secrets
from datetime import datetime


class User:
    def __init__(self, user_id, username, password):
        self._user_id = user_id
        self._username = username
        self._salt = secrets.token_hex(8)
        self._hashed_password = self._hash(password, self._salt)
        self._registration_date = datetime.now().isoformat()

    def _hash(self, password, salt):
        return hashlib.sha256((password + salt).encode()).hexdigest()

    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, new_username):
        if not new_username or not new_username.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = new_username

    def get_user_info(self):
        print(f"Пользователь: {self._username} (id={self._user_id})")
        print(f"Зарегистрирован: {self._registration_date}")

    def change_password(self, new_password):
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._salt = secrets.token_hex(8)
        self._hashed_password = self._hash(new_password, self._salt)

    def verify_password(self, password):
        return self._hash(password, self._salt) == self._hashed_password