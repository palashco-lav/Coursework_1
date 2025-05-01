import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

import src.utils as utils

base_dir = Path(__file__).resolve().parent.parent

logger_utils = logging.getLogger(__name__)
logger_utils.setLevel(logging.DEBUG)

# настройка обработчика и форматировщика для logger_masks
handler_utils = logging.FileHandler(f"{Path(__file__).resolve().parent.parent}\\utils.log", mode="w", encoding="utf-8")
formatter_utils = logging.Formatter("%(asctime)s %(filename)s %(levelname)s: %(message)s")

# добавление форматировщика к обработчику
handler_utils.setFormatter(formatter_utils)
# добавление обработчика к логгеру
logger_utils.addHandler(handler_utils)


def function_for_home_page(data_in: str) -> dict:
    """
    Страница «Главная»
    Функция для сбора и обработки данных, необходимых для отображения на главной странице приложения.

    Параметры:
    data_in (str): строка с датой и временем в формате 'YYYY-MM-DD HH:MM:SS' для указания периода анализа.
        Если не указана, используется текущая дата и время.

    Возвращает:
    dict: словарь с собранными данными, включая приветственное сообщение, информацию о последней использованной карте,
        топ-транзакции, курсы валют и цены акций.

    Описание:
    Функция выполняет следующие действия:
    1. Определяет дату начала отчётного периода (начало текущего месяца) и текущую дату.
    2. Формирует приветственное сообщение с использованием функции get_greeting().
    3. Читает данные о транзакциях из файла Excel.
    4. Получает информацию о последней использованной карте и общем кешбэке за отчётный период.
    5. Находит топ-транзакции за отчётный период.
    6. Загружает пользовательские настройки, включая список интересующих валют и акций.
    7. Получает текущие курсы валют и цены акций.
    8. Возвращает словарь с собранными данными.

    Примеры использования:
    >>> function_for_home_page("2024-01-15 12:00:00")
    {
        'greeting': ['Доброе день'],
        'card': {'last_digits': '3456', 'total_spent': 300.0, 'cashback': 3.0},
        'top_transactions': {'date': '2024.01.15',
                             'amount': 500.0,
                             'category': 'Shopping',
                             'description': 'Groceries'},
        'currency_rates': {'currency': 'USD', 'rate': 90.0},
        'stock_prices': {'stock': 'AAPL', 'price': 150.12}
    }
    """
    operation_date = datetime.now()
    if data_in is not None:
        operation_date = datetime.strptime(data_in, "%Y-%m-%d %H:%M:%S")

    start_date = operation_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_date_ts = pd.to_datetime(start_date)
    operation_date_ts = pd.to_datetime(operation_date)

    # Формирую приветственное сообщение
    data_out: dict = {}
    data_out["greeting"] = []
    data_out["greeting"].append(utils.get_greeting())

    read_data = pd.read_excel(f"{base_dir}\\data\\operations.xlsx")

    data_out["card"] = []
    data_out["card"].append(utils.get_last_card_total_cashback(read_data, start_date_ts, operation_date_ts))

    result_dict = utils.get_top_transactions(read_data)
    data_out["top_transactions"] = []
    data_out["top_transactions"].append(result_dict)

    user_settings = utils.load_user_settings()
    currencies = user_settings["user_currencies"]
    user_stocks = user_settings["user_stocks"]

    data_out["currency_rates"] = []
    data_out["currency_rates"].append(utils.get_currency_rates(currencies))

    data_out["stock_prices"] = []
    data_out["stock_prices"].append(utils.get_stock_prices(user_stocks))

    return data_out
