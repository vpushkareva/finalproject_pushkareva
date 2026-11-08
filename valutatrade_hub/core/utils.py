import json
import os

DATA_DIR = "data"


def load_data(filename, default):
    """Читает JSON из data/<файл>, нет файла — возвращает default."""
    try:
        with open(f"{DATA_DIR}/{filename}", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_data(filename, data):
    """Сохраняет data в data/<файл>, создав папку при необходимости."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(f"{DATA_DIR}/{filename}", "w") as f:
        json.dump(data, f, indent=2)


def parse_amount(value):
    """Даёт float из строки, мусор и неположительные числа — ошибка."""
    amount = float(value)
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return amount


def convert(amount, rate):
    """Переводит сумму по курсу."""
    return amount * rate
