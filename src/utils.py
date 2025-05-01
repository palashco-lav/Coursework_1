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
    """
    Функция для получения приветствия в зависимости от времени суток.

    Возвращает:
    str: сообщение приветствия, которое может быть "Доброе утро", "Добрый день" или "Доброй ночи"
    в зависимости от текущего часа.

    Примеры:
    >>> get_greeting()  # Предположим, что сейчас 10:00
    'Доброе утро'
    >>> get_greeting()  # Предположим, что сейчас 15:00
    'Добрый день'
    >>> get_greeting()  # Предположим, что сейчас 23:00
    'Доброй ночи'
    """
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
    Функция для получения данных о последних 4-х цифрах номера карты,
    общей сумме расходов и кешбэке (1 рубль на каждые 100 рублей) за указанный период.

    Параметры:
    read_data (pd.DataFrame): данные для обработки,
    должны содержать столбцы "Дата операции", "Категория", "Сумма операции" и "Номер карты".
    start_date_ts (pd.DatetimeIndex | pd.Timestamp | datetime): начало интервала обработки.
    operation_date_ts (pd.DatetimeIndex | pd.Timestamp | datetime): дата конца обработки.

    Возвращает:
    list: список словарей с данными о последних 4-х цифрах номера карты, общей сумме расходов и кешбэке.

    Примеры:
    >>> data = pd.DataFrame(
    ...     {
    ...         "Дата операции": ["01.01.2024 10:00:00", "02.01.2024 11:00:00"],
    ...         "Категория": ["Покупка", "Покупка"],
    ...         "Сумма операции": [-100.0, -200.0],
    ...         "Номер карты": ["1234567890123456", "1234567890123456"]
    ...     }
    ... )
    >>> get_last_card_total_cashback(data, pd.to_datetime("01.01.2024"), pd.to_datetime("02.01.2024"))
    [{'last_digits': '3456', 'total_spent': 300.0, 'cashback': 3.0}]
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
    Функция загружает пользовательские настройки из файла user_settings.json.

    Возвращает:
    dict: словарь с пользовательскими настройками, если файл успешно загружен и содержит словарь.
    В случае возникновения ошибок (файл не найден, некорректный формат JSON или данные не являются словарем)
    возвращается пустой словарь.

    Примеры:
    >>> load_user_settings()
    {'username': 'example_user', 'theme': 'dark'}
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

    Параметры:
    file_path (str): путь к файлу XLSX, содержащему данные о финансовых операциях.

    Возвращает:
    list: список словарей, где каждый словарь представляет собой строку данных из XLSX файла в формате ключ-значение.

    Описание:
    Функция открывает указанный XLSX файл, считывает данные с первого листа и преобразует их в список словарей.
    Каждый словарь в списке соответствует строке данных из файла, где ключи словаря
     - это названия столбцов, а значения - данные из соответствующих ячеек.

    Примеры использования:
    >>> read_financial_trans_xlsx('path/to/file.xlsx')
    [{'Date': '2023-01-01', 'Amount': 100.0, 'Description': 'First transaction'},
     {'Date': '2023-01-02', 'Amount': 200.0, 'Description': 'Second transaction'}]
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
    Функция для получения топ-5 транзакций по сумме платежа.

    Параметры:
    df (pd.DataFrame): входной датафрейм с данными о транзакциях, который должен содержать столбцы:
        - «Дата операции» (тип datetime)
        - «Сумма операции» (числовой тип)
        - «Категория» (строковый тип)
        - «Описание» (строковый тип)

    Возвращает:
    dict: словарь с информацией о топ-транзакциях, включая следующие поля для каждой транзакции:
        - date: дата операции в формате YYYY.MM.DD
        - amount: сумма операции (по модулю)
        - category: категория транзакции
        - description: описание транзакции

    Описание:
    Функция выполняет проверку корректности входного датафрейма, включая тип данных,
    наличие необходимых столбцов и их типы.
    Затем она извлекает топ-5 транзакций с наименьшей суммой платежа и формирует словарь с деталями этих транзакций.

    Примеры использования:
    >>> df = pd.DataFrame({
    ...     'Дата операции': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03',
                                             '2023-01-04', '2023-01-05', '2023-01-06']),
    ...     'Сумма операции': [-100, -200, -50, -300, -150, -250],
    ...     'Категория': ['A', 'B', 'A', 'B', 'A', 'B'],
    ...     'Описание': ['Op1', 'Op2', 'Op3', 'Op4', 'Op5', 'Op6']
    ... })
    >>> get_top_transactions(df)
    {'date': '2023.01.03', 'amount': 50, 'category': 'A', 'description': 'Op3'}
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
    test_data = df["Категория"]
    for category in test_data:
        if not isinstance(category, str):
            if not isinstance(category, float):
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
    """
    Функция для получения курсов валют с сервера Центрального банка России.

    Параметры:
    currencies (list): список кодов валют, для которых нужно получить курсы.

    Возвращает:
    list: список словарей, где каждый словарь содержит код валюты и её курс.

    Описание:
    Функция отправляет GET-запрос на сервер Центрального банка России для получения JSON с курсами валют.
    Затем она проверяет структуру полученных данных и, если всё корректно, перебирает список переданных валют,
    получает их курсы и добавляет в результат. Если валюта не найдена в данных с сервера, выводится предупреждение.
    В случае ошибок при запросе или обработке данных функция генерирует соответствующие исключения.

    Примеры использования:
    >>> get_currency_rates(["USD", "EUR"])
    [{"currency": "USD", "rate": 90.0}, {"currency": "EUR", "rate": 100.0}]
    """
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
