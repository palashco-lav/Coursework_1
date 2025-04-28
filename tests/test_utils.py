import pandas as pd
import json
from datetime import datetime
from unittest.mock import patch, Mock
import unittest.mock as mock
import unittest
import numpy as np
import pytest
import os

from src.utils import (get_top_transactions, get_last_card_total_cashback, get_currency_rates,
                       read_financial_trans_xlsx, load_user_settings, get_greeting, get_stock_prices)


def test_get_greeting_morning():
    # Создаем фиктивное время для утреннего приветствия
    mock_time = datetime(2025, 4, 21, 8, 0, 0)

    # Мокаем datetime.now()
    with mock.patch('src.utils.datetime.now') as mock_now:
        mock_now.return_value = mock_time

        # Вызываем тестируемую функцию
        result = get_greeting()

        # Проверяем результат
        assert result == "Доброе утро", "Ожидалось 'Доброе утро' для утреннего времени"


def test_get_greeting_day():
    # Создаем фиктивное время для дневного приветствия
    mock_time = datetime(2025, 4, 21, 14, 0, 0)

    # Мокаем datetime.now()
    with mock.patch('src.utils.datetime.now') as mock_now:
        mock_now.return_value = mock_time

        # Вызываем тестируемую функцию
        result = get_greeting()

        # Проверяем результат
        assert result == "Добрый день", "Ожидалось 'Добрый день' для дневного времени"


def test_get_greeting_night():
    # Создаем фиктивное время для ночного приветствия
    mock_time = datetime(2025, 4, 21, 23, 0, 0)

    # Мокаем datetime.now()
    with mock.patch('src.utils.datetime.now') as mock_now:
        mock_now.return_value = mock_time

        # Вызываем тестируемую функцию
        result = get_greeting()

        # Проверяем результат
        assert result == "Доброй ночи", "Ожидалось 'Доброй ночи' для ночного времени"


# Фикстура для создания тестового датафрейма
@pytest.fixture
def test_dataframe():
    data = {
        'Дата операции': ['01.04.2025 10:00:00', '02.04.2025 11:00:00', '03.04.2025 12:00:00', '04.04.2025 13:00:00'],
        'Категория': ['Продукты', 'Одежда', 'Продукты', 'Развлечения'],
        'Сумма операции': [-1000, -2000, -1500, -2500],
        'Номер карты': ['4111111111111111', '4111111111111111', '4222222222222222', '4222222222222222']
    }
    return pd.DataFrame(data)


# Фикстура для создания дат
@pytest.fixture
def test_dates():
    start_date = pd.to_datetime('2025-04-01')
    end_date = pd.to_datetime('2025-04-05')
    return start_date, end_date


# Тестовый кейс для проверки корректности работы функции
@pytest.mark.parametrize("start_date, end_date, expected_result", [
    (
            pd.to_datetime('2025-04-01'),
            pd.to_datetime('2025-04-05'),
            [
                {'last_digits': '1111', 'total_spent': 3000.00, 'cashback': 30.00},
                {'last_digits': '2222', 'total_spent': 4000.00, 'cashback': 40.00}
            ]
    )
])
def test_get_last_card_total_cashback(test_dataframe, start_date, end_date, expected_result):
    result = get_last_card_total_cashback(test_dataframe, start_date, end_date)
    assert result == expected_result


# Тестовый кейс для проверки валидации столбцов
def test_missing_columns(test_dataframe, test_dates):
    df = test_dataframe.drop(columns=['Категория'])
    start_date, end_date = test_dates

    with pytest.raises(ValueError):
        get_last_card_total_cashback(df, start_date, end_date)


# Тестовый кейс для проверки валидации формата даты
def test_incorrect_date_format(test_dataframe):
    start_date = '2025-04-01'  # Некорректный формат
    end_date = '2025-04-05'  # Некорректный формат

    with pytest.raises(TypeError):
        get_last_card_total_cashback(test_dataframe, start_date, end_date)


# Тестовый кейс для проверки обработки пустых данных
def test_empty_dataframe(test_dates):
    df = pd.DataFrame()
    start_date, end_date = test_dates

    result = get_last_card_total_cashback(df, start_date, end_date)
    assert result == []


# Тестовый кейс для проверки обработки некорректных номеров карт
def test_invalid_card_numbers(test_dataframe, test_dates):
    df = test_dataframe.copy()
    df['Номер карты'] = ['1234', '5678', '91011', '123456789012345']  # Некорректные номера
    start_date, end_date = test_dates

    result = get_last_card_total_cashback(df, start_date, end_date)
    assert result == []

def test_load_user_settings_success():
    # Создаем тестовые данные
    test_settings = {'name': 'Иван', 'theme': 'dark'}, {'name': 'Петр', 'theme': 'light'}


    # Мокаем функцию open()
    with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(test_settings))) as mock_file:
        # Вызываем тестируемую функцию
        result = load_user_settings()

        # Проверяем результат
        assert result == test_settings, "Результаты не совпадают с ожидаемыми"

        # Проверяем, что файл был открыт с правильными параметрами
        mock_file.assert_called_once_with(
            mock.ANY, "r", encoding="utf-8"
        )


def test_load_user_settings_file_not_found():
    # Мокаем исключение FileNotFoundError
    with mock.patch('builtins.open', side_effect=FileNotFoundError):
        # Вызываем тестируемую функцию
        result = load_user_settings()

        # Проверяем результат
        assert result == [], "Ожидался пустой список при ошибке FileNotFoundError"


def test_load_user_settings_json_decode_error():
    # Мокаем некорректный JSON
    with mock.patch('builtins.open', mock.mock_open(read_data="некорректный JSON")):
        # Вызываем тестируемую функцию
        result = load_user_settings()

        # Проверяем результат
        assert result == [], "Ожидался пустой список при ошибке JSONDecodeError"


def test_load_user_settings_wrong_type():
    # Тестируем случай, когда данные не являются списком
    with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps({'wrong': 'data'}))):
        # Вызываем тестируемую функцию
        result = load_user_settings()

        # Проверяем результат
        assert result == [], "Ожидался пустой список при неверном типе данных"

def test_read_financial_trans_xlsx():
# Подготавливаем тестовые данные
    test_data = [
        {'date': '2025-04-21', 'amount': 1000, 'description': 'Зарплата'},
        {'date': '2025-04-22', 'amount': -200, 'description': 'Покупка'}
    ]

    # Создаем моки для pandas
    with mock.patch('src.utils.pd.read_excel') as mock_read_excel:
        # Настраиваем поведение моков
        mock_df = mock.Mock()
        mock_df.to_dict.return_value = test_data
        mock_read_excel.return_value = mock_df

        # Вызываем тестируемую функцию
        result = read_financial_trans_xlsx('test_file_path.xlsx')

        # Проверяем вызовы
        mock_read_excel.assert_called_once_with('test_file_path.xlsx', sheet_name=0)

        # Проверяем результат
        assert result == test_data, "Результаты не совпадают с ожидаемыми"


def test_read_financial_trans_xlsx_empty_file():
    with mock.patch('src.utils.pd.read_excel') as mock_read_excel:
        # Тестируем случай с пустым файлом
        mock_read_excel.return_value = pd.DataFrame()

        result = read_financial_trans_xlsx('empty_file.xlsx')

        assert result == [], "Ожидался пустой список для пустого файла"


def test_read_financial_trans_xlsx_error():
    with mock.patch('src.utils.pd.read_excel') as mock_read_excel:
        # Тестируем обработку ошибки при чтении файла
        mock_read_excel.side_effect = Exception('File not found')

        try:
            read_financial_trans_xlsx('non_existent_file.xlsx')
        except Exception as e:
            assert 'File not found' in str(e), "Ошибка не была обработана корректно"
        else:
            assert False, "Ожидалось исключение, но его не было"


def setUp(self):
    # Создаем тестовый датафрейм
    self.test_data = pd.DataFrame({
        'Дата операции': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
        'Сумма операции': [-100, -200, -300, -400, -500],
        'Категория': ['Еда', 'Транспорт', 'Развлечения', 'Товары', 'Услуги'],
        'Описание': ['Покупка в магазине', 'Поездка на такси', 'Кинотеатр', 'Супермаркет', 'Ремонт']
    })

@patch('transactions.pd.DataFrame.nsmallest')
def test_get_top_transactions(self, mock_nsmallest):
    # Настраиваем макет для метода nsmallest
    mock_nsmallest.return_value = self.test_data.head(5)

    # Вызываем тестируемую функцию
    result = get_top_transactions(self.test_data)

    # Проверяем, что метод nsmallest был вызван с правильными параметрами
    mock_nsmallest.assert_called_once_with(5, 'Сумма операции')

    # Проверяем структуру возвращаемого результата
    self.assertIsInstance(result, dict)
    self.assertIn('top_transactions', result)
    self.assertIsInstance(result['top_transactions'], list)
    self.assertEqual(len(result['top_transactions']), 5)

    # Проверяем содержимое первой транзакции
    first_transaction = result['top_transactions'][0]
    self.assertEqual(first_transaction['top_transactions']['date'], '2025.01.01')
    self.assertEqual(first_transaction['top_transactions']['amount'], 100)
    self.assertEqual(first_transaction['top_transactions']['category'], 'Еда')
    self.assertEqual(first_transaction['top_transactions']['description'], 'Покупка в магазине')

def test_get_top_transactions_empty_df(self):
    # Создаем пустой датафрейм
    empty_df = pd.DataFrame()

    # Вызываем функцию с пустым датафреймом
    result = get_top_transactions(empty_df)

    # Проверяем результат
    self.assertIsInstance(result, dict)
    self.assertIn('top_transactions', result)
    self.assertEqual(len(result['top_transactions']), 0)


import pytest
import requests
from unittest.mock import patch, Mock


# Фикстура для создания тестовых данных
@pytest.fixture
def test_cbr_data():
    return {
        "Valute": {
            "USD": {"Value": 90.0},
            "EUR": {"Value": 100.0},
            "BTC": {"Value": 50000.0},
            "RUB": {"Value": 1.0}
        }
    }


# Тестовый кейс для успешного получения курсов
@pytest.mark.parametrize("currencies, expected_result", [
    (["USD", "EUR"], [{"currency": "USD", "rate": 90.0}, {"currency": "EUR", "rate": 100.0}]),
    (["BTC"], [{"currency": "BTC", "rate": 50000.0}]),
    (["RUB"], [{"currency": "RUB", "rate": 1.0}])
])
def test_get_currency_rates_success(currencies, expected_result, test_cbr_data):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.return_value = test_cbr_data

        result = get_currency_rates(currencies)

        assert result == expected_result


# Тестовый кейс для проверки несуществующих валют
@pytest.mark.parametrize("currencies, expected_result", [
    (["USD", "XYZ"], [{"currency": "USD", "rate": 90.0}]),
    (["ABC", "DEF"], [])
])
def test_get_currency_rates_non_existent(currencies, expected_result, test_cbr_data):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.return_value = test_cbr_data

        result = get_currency_rates(currencies)

        assert result == expected_result


# Тестовый кейс для проверки ошибок при получении данных
def test_get_currency_rates_request_error(test_cbr_data):
    with patch('requests.get') as mocked_get:
        mocked_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(requests.RequestException):
            get_currency_rates(["USD"])


# Тестовый кейс для проверки некорректного формата ответа
def test_get_currency_rates_invalid_response(test_cbr_data):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.side_effect = ValueError("Invalid JSON")

        with pytest.raises(ValueError):
            get_currency_rates(["USD"])


# Тестовый кейс для проверки пустого списка валют
def test_get_currency_rates_empty_list(test_cbr_data):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.return_value = test_cbr_data

        result = get_currency_rates([])

        assert result == []


# Тестовый кейс для проверки некорректного типа входных данных
def test_get_currency_rates_invalid_input():
    with pytest.raises(TypeError):
        get_currency_rates("USD")  # Ожидаем список, получаем строку


# Тестовый кейс для проверки отсутствия данных о валютах
def test_get_currency_rates_empty_valute(test_cbr_data):
    empty_data = {"Valute": {}}
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.return_value = empty_data

        result = get_currency_rates(["USD"])

        assert result == []


# Фикстура для создания тестовых данных
@pytest.fixture
def test_stock_data():
    return {
        "Global Quote": {
            "05. price": "150.12",
            "01. symbol": "AAPL"
        }
    }


# Тестовый кейс для успешного получения цен акций
@pytest.mark.parametrize("stocks, expected_result", [
    (["AAPL"], [{"stock": "AAPL", "price": 150.12}]),
    (["AMZN", "TSLA"], [{"stock": "AMZN", "price": 3173.18}, {"stock": "TSLA", "price": 220.50}]),
    (["GOOGL"], [{"stock": "GOOGL", "price": 1200.75}])
])
def test_get_stock_prices_success(stocks, expected_result, test_stock_data):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.return_value = test_stock_data

        with patch('dotenv.load_dotenv') as mocked_load_dotenv:
            mocked_load_dotenv.return_value = None
            os.environ["BASE_URL"] = "https://www.alphavantage.co/query"
            os.environ["API_KEY"] = "demo_key"

            result = get_stock_prices(stocks)

            assert result == expected_result


# Тестовый кейс для проверки несуществующих тикеров
@pytest.mark.parametrize("stocks", [
    ["XYZ"],
    ["ABC", "DEF"]
])
def test_get_stock_prices_non_existent(stocks, test_stock_data):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.return_value = {"Error Message": "Symbol does not exist"}

        with patch('dotenv.load_dotenv'):
            os.environ["BASE_URL"] = "https://www.alphavantage.co/query"
            os.environ["API_KEY"] = "demo_key"

            result = get_stock_prices(stocks)

            assert result == []


# Тестовый кейс для проверки ошибок при получении данных
def test_get_stock_prices_request_error(test_stock_data):
    with patch('requests.get') as mocked_get:
        mocked_get.side_effect = requests.RequestException("Network error")

        with patch('dotenv.load_dotenv'):
            os.environ["BASE_URL"] = "https://www.alphavantage.co/query"
            os.environ["API_KEY"] = "demo_key"

            with pytest.raises(requests.RequestException):
                get_stock_prices(["AAPL"])


# Тестовый кейс для проверки некорректного формата ответа
def test_get_stock_prices_invalid_response(test_stock_data):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.side_effect = ValueError("Invalid JSON")

        with patch('dotenv.load_dotenv'):
            os.environ["BASE_URL"] = "https://www.alphavantage.co/query"
            os.environ["API_KEY"] = "demo_key"

            with pytest.raises(ValueError):
                get_stock_prices(["AAPL"])


# Тестовый кейс для проверки пустого списка тикеров
def test_get_stock_prices_empty_list(test_stock_data):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.json.return_value = test_stock_data

        with patch('dotenv.load_dotenv'):
            os.environ["BASE_URL"] = "https://www.alphavantage.co/query"
            os.environ["API_KEY"] = "demo_key"

            result = get_stock_prices([])

            assert result == []