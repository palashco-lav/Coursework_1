import json
import logging
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

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


# Функция для получения приветствия
def get_greeting() -> str:
    result: str
    time = datetime.now()
    logger_utils.debug(f'Текущее время: "{time.strftime("%Y-%m-%d %H:%M:%S")}')
    if 4 <= time.hour < 12:

        result = "Доброе утро"
    elif 12 <= time.hour < 18:
        result = "Добрый день"
    else:
        result = "Доброй ночи"
    logger_utils.debug(f'Сообщение приветствия: "{result}"')
    return result


def get_last_card_total_cashback(
    read_data: pd.DataFrame,
    start_date_ts: pd.DatetimeIndex | pd.Timestamp | datetime,
    operation_date_ts: pd.DatetimeIndex | pd.Timestamp | datetime,
) -> list:
    """
    Функция получения данных о последних 4-х цифрах номера карты, общая сумма расходов,
    кешбэк (1 рубль на каждые 100 рублей)
    :param read_data:   данные для обработки
    :param start_date_ts:   начало интервала обработки
    :param operation_date_ts:   датае конца обработки
    :return:
    """
    # Находим дату начала отчётного периода - начало месяца
    # Проверяем наличие необходимых столбцов
    required_columns = ["Дата операции", "Категория", "Сумма операции"]
    if not set(required_columns).issubset(read_data.columns):
        raise ValueError("Датафрейм должен содержать столбцы: Дата операции, Категория, Сумма операции")
    # Проверяем наличие данных в стобцах
    if read_data.empty:
        raise ValueError("Столбцы Датафрейма должны быть заполнены")
    # Проверяем корректность дат
    if start_date_ts > operation_date_ts:
        raise ValueError("Некорректная дата окончания (раньше начала)")

    read_data["Дата операции"] = pd.to_datetime(read_data["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    logger_utils.debug(
        f'Обрабатываем данные с {start_date_ts.strftime("%Y-%m-%d %H:%M:%S")} по\
{operation_date_ts.strftime("%Y-%m-%d %H:%M:%S")}'
    )
    # Оставляем данные только после начала отчётного периода
    read_data = read_data[(read_data["Дата операции"] >= start_date_ts)]
    # Также удаляем данные после входящей даты
    end_operation_date_ts = operation_date_ts + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    read_data = read_data[(read_data["Дата операции"] <= end_operation_date_ts)]

    # формирую передачу данных о: последние 4 цифры карты; общая сумма расходов; кешбэк (1 рубль на каждые 100 рублей).
    user_card = read_data["Номер карты"].unique().tolist()
    card_dict = {}

    if len(read_data) != 0:
        result = []
        for card in user_card:
            if isinstance(card, str) and len(card) >= 4 and card[-4:].isdigit():
                # фильтрую только операции по данной карте
                card_data = read_data[(read_data["Номер карты"] == card)]
                card_dict["last_digits"] = card[-4:]
                card_dict["total_spent"] = round(card_data["Сумма операции"].sum() * -1, 2)
                card_dict["cashback"] = card_dict["total_spent"] / 100
                logger_utils.debug(
                    f"Отфильтрованные данные: "
                    f'   Последние 4 цифры номера карты {card_dict["last_digits"]}'
                    f'   Сумма операции: {card_dict["total_spent"]}'
                    f"   Кешбэк"
                )
                result.append(card_dict)
    else:
        result = []
        card_dict["last_digits"] = None
        card_dict["total_spent"]: int = 0
        card_dict["cashback"]: int | float = 0
        logger_utils.debug(
            f"Отфильтрованные данные: "
            f'   Последние 4 цифры номера карты {card_dict["last_digits"]}'
            f'   Сумма операции: {card_dict["total_spent"]}'
            f"   Кешбэк"
        )
        result.append(card_dict)
    return result


def load_user_settings() -> dict:
    """
    Функция загружающая пользовательские данные
    :return:
    """
    file_path = f"{base_dir}//user_settings.json"
    try:
        logger_utils.debug(f'Попытка открыть файл: "{file_path}"')
        # открываем файл
        with open(file_path, "r", encoding="utf-8") as f:
            logger_utils.debug(f'Файл успешно открыт: "{file_path}"')
            transaction_data = json.load(f)
            if isinstance(transaction_data, dict):
                # если тип данных список - возвращаем список
                logger_utils.debug("Файл содержит словарь - функция возвращает значение словарь")
                return transaction_data
            else:
                # если не список - возвращаем пустой список
                logger_utils.debug("Файл содержит список - функция возвращает пустой список")
                return {}
    except FileNotFoundError:
        # файл не найдем - возвращаю пустой список
        logger_utils.error(f'Файл: "{file_path}" не найден - возвращаю пустой список')
        return {}
    except json.decoder.JSONDecodeError:
        logger_utils.error(f'JSON файл: "{file_path}" не декодировался - возвращаю пустой список')
        # JSON файл не декодировался - возвращаю пустой список
        return {}


def read_financial_trans_xlsx(file_path: str) -> list:
    """
    Функция для считывания финансовых операций из XLSX файла.

    :param file_path: путь к файлу
    :return: список словарей с данными финансовых операций
    """
    try:
        with pd.ExcelFile(file_path) as xlsx_file:
            logger_utils.debug(f'Открыт XLSX файл: "{file_path}"')
            df = pd.read_excel(xlsx_file, sheet_name=0)
            dict_list = df.to_dict(orient="records")
            return dict_list
    except FileNotFoundError as e:
        logger_utils.error(f"Файл не найден: {e}")
        raise e


def get_top_transactions(df: pd.DataFrame) -> dict:
    """
    Функция для получения топ-5 транзакций по сумме платежа

    Параметры:
    df (pd.DataFrame): входной датафрейм с данными о транзакциях

    Возвращает:
    dict: словарь с информацией о топ-транзакциях
    """
    # Проверка типа входного параметра
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Входной параметр должен быть типа pd.DataFrame")

    # Проверка на пустой датафрейм
    if df.empty:
        raise ValueError("Датафрейм не должен быть пустым")

    # Проверка наличия необходимых столбцов
    required_columns = {"Дата операции", "Сумма операции", "Категория", "Описание"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Датафрейм должен содержать столбцы: {', '.join(required_columns)}")
    # Проверка типов данных в столбцах
    if not pd.api.types.is_datetime64_dtype(df["Дата операции"].dtype):
        raise TypeError("Столбец 'Дата операции' должен содержать значения типа datetime")
    if not np.issubdtype(df["Сумма операции"].dtype, np.number):
        raise TypeError("Столбец 'Сумма операции' должен содержать числовые значения")
    if not pd.api.types.is_string_dtype(df["Категория"]):
        raise TypeError("Столбец 'Сумма Категория' должен строку")
    # Получаем топ-5 минимальных значений по сумме операции

    min_values = df.nsmallest(5, "Сумма операции")
    top_transactions_dict = {}

    # Перебираем строки и формируем словарь
    logger_utils.debug("Формируем словарь топ-5 транзакций:")
    for index, row in min_values.iterrows():

        # Формируем словарь с нужными полями
        top_transactions_dict = {
            "date": row["Дата операции"],
            "amount": row["Сумма операции"] * -1,
            "category": row["Категория"],
            "description": row["Описание"],
        }

        # Форматируем дату
        top_transactions_dict["date"] = top_transactions_dict["date"].strftime("%Y.%m.%d")

        logger_utils.debug(
            f"   Дата операции: {top_transactions_dict['date']}"
            f"   Сумма операции: {top_transactions_dict['amount']}"
            f"   Категория: {top_transactions_dict['category']}"
            f"   Описание: {top_transactions_dict['description']}"
        )

        # Добавляем в выходной список
        # data_out.append(top_transactions_dict)

    return top_transactions_dict


def get_currency_rates(currencies: list) -> list:
    try:
        # Получаем JSON с сервера ЦБ
        logger_utils.debug(
            "Запрашиваю данные по курсам валют с сервера ЦБ: https://www.cbr-xml-daily.ru/daily_json.js"
        )
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
        response.raise_for_status()  # Проверка на успешность запроса
        data = response.json()

        # Валидация структуры данных
        if not isinstance(data, dict) or "Valute" not in data:
            logger_utils.error("Некорректный формат данных с сервера ЦБ")
            raise ValueError("Некорректный формат данных")

        # Создаем список для хранения результатов
        result = []

        # Перебираем список нужных валют
        logger_utils.debug("Получаем список нужных валют")
        for currency in currencies:
            # Проверяем наличие валюты в данных
            if currency in data["Valute"]:
                # Получаем курс валюты
                rate = data["Valute"][currency]["Value"]
                logger_utils.debug(f"Валюта: {currency} курс: {rate}")
                # Добавляем в результат
                result.append({"currency": currency, "rate": rate})
            else:
                logger_utils.warning(f"Валюта {currency} не найдена в данных ЦБ")

        return result

    except requests.exceptions.RequestException as e:
        logger_utils.error(f"Ошибка при запросе данных: {str(e)}")
        raise Exception("Network error")

    except (KeyError, ValueError, TypeError) as e:
        logger_utils.error(f"Ошибка обработки данных: {str(e)}")
        raise ValueError("Ошибка обработки данных")  # Добавляем явное исключение ValueError


def get_stock_prices(user_stocks: list) -> list:
    """
    Функция для получения текущих цен акций через Alpha Vantage API

    Параметры:
    user_stocks - список тикеров акций
    api_key - ключ доступа к Alpha Vantage API

    Возвращает:
    Список словарей с данными о ценах акций в формате:
    [
        {"stock": "AAPL", "price": 150.12},
        {"stock": "AMZN", "price": 3173.18},
        ...
    ]
    """

    # Загрузка переменных из .env-файла
    load_dotenv()

    # URL для запроса
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")

    # Результат будем сохранять здесь
    result = []
    logger_utils.debug(f"Запрашиваю данные по ценным бумагам: {base_url}")

    # Делаем запросы для каждой акции
    for stock in user_stocks:
        params = {"function": "GLOBAL_QUOTE", "symbol": stock, "apikey": api_key}

        response = requests.get(base_url, params=params)
        data = response.json()

        # Проверяем наличие данных
        if "Global Quote" in data:
            price = float(data["Global Quote"]["05. price"])
            result.append({"stock": stock, "price": price})
            logger_utils.debug(f"Цена акции {stock}: {price}")
        else:
            print(f"Ошибка получения данных для {stock}: {data}")
            logger_utils.debug(f"Ошибка получения данных для {stock}: {data}")

    return result
