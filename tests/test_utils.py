import pytest
import json
import pandas as pd
from datetime import datetime
from unittest.mock import patch, Mock, mock_open
from src.utils import get_greeting, get_last_card_total_cashback, load_user_settings, get_top_transactions,\
get_currency_rates, get_stock_prices


# Фикстура для создания тестовых временных меток
@pytest.fixture(params=[
    (datetime(2025, 4, 30, 5, 0, 0), "Доброе утро"),
    (datetime(2025, 4, 30, 13, 0, 0), "Добрый день"),
    (datetime(2025, 4, 30, 23, 0, 0), "Доброй ночи")
])
def test_time(request):
    return request.param


# Параметризированный тест
@pytest.mark.parametrize("hour,expected_greeting", [
    (5, "Доброе утро"),  # Утро
    (13, "Добрый день"),  # День
    (23, "Доброй ночи")  # Ночь
])
def test_get_greeting(hour, expected_greeting):
    # Создаем фиктивную дату с заданным часом
    test_datetime = datetime(2025, 4, 30, hour, 0, 0)

    # Заменяем datetime.now() на фиктивную дату
    with patch('src.utils.datetime') as mock_datetime:
        mock_datetime.now.return_value = test_datetime

        # Проверяем результат
        result = get_greeting()
        assert result == expected_greeting


# Тест с использованием фикстуры
def test_get_greeting_with_fixture(test_time):
    test_datetime, expected_greeting = test_time

    with patch('src.utils.datetime') as mock_datetime:
        mock_datetime.now.return_value = test_datetime

        result = get_greeting()
        assert result == expected_greeting


# Тест граничных значений
def test_get_greeting_boundary_values_():
    with patch('src.utils.datetime') as mock_datetime:
        # Проверка на границе "утро" и "день"
        mock_datetime.now.return_value = datetime(2025, 4, 30, 12, 0, 0)
        assert get_greeting() == "Добрый день"

        # Проверка на границе "день" и "ночь"
        mock_datetime.now.return_value = datetime(2025, 4, 30, 18, 0, 0)
        assert get_greeting() == "Доброй ночи"

        # Проверка на границе "ночь" и "утро"
        mock_datetime.now.return_value = datetime(2025, 4, 30, 4, 0, 0)
        assert get_greeting() == "Доброе утро"


# Фикстура для создания тестового датафрейма
@pytest.fixture
def test_dataframe():
    data = {
        'Дата операции': ['01.04.2025 10:00:00', '02.04.2025 11:00:00', '03.04.2025 12:00:00'],
        'Категория': ['Продукты', 'Одежда', 'Развлечения'],
        'Сумма операции': [-1000, -2000, -1500],
        'Номер карты': ['4111111111111111', '4111111111111111', '4111111111111111']
    }
    return pd.DataFrame(data)


# Тестовый параметр для проверки корректности входных данных
@pytest.mark.parametrize("start_date, end_date, expected_total_spent, expected_cashback, card_digit", [
    (datetime(2025, 4, 1), datetime(2025, 4, 4), 4500, 45.0, '1111'),  # Все операции попадают в период
    (datetime(2025, 4, 2), datetime(2025, 4, 3), 3500, 35.0, '1111'),  # Только две операции попадают
    (datetime(2025, 4, 4), datetime(2025, 4, 4),     0, 0.0, None)  # Нет операций в периоде
])
def test_get_last_card_total_cashback(test_dataframe, start_date, end_date, expected_total_spent,
                                      expected_cashback, card_digit):
    # Патч логгера для избежания вывода в консоль
    with patch('src.utils.logger_utils.debug') as mock_logger:
        result = get_last_card_total_cashback(test_dataframe, start_date, end_date)

        # Проверяем возвращаемые значения
        test_result = card_digit
        assert result[0]['last_digits'] == test_result
        test_result = expected_total_spent
        assert result[0]['total_spent'] == test_result
        test_result = expected_cashback
        assert result[0]['cashback'] == test_result

        # Проверяем вызовы логгера
        mock_logger.assert_called()


# Тест на проверку валидации столбцов
def test_missing_columns(test_dataframe):
    # Удаляем необходимый столбец
    del test_dataframe['Категория']

    with pytest.raises(ValueError):
        get_last_card_total_cashback(test_dataframe, datetime(2025, 4, 1), datetime(2025, 4, 4))


# Тест на проверку обработки нескольких карт
def test_multiple_cards(test_dataframe):
    # Добавляем операции по другой карте
    additional_data = {
        'Дата операции': ['04.04.2025 13:00:00'],
        'Категория': ['Транспорт'],
        'Сумма операции': [-3000],
        'Номер карты': ['4222222222222222']
    }
    test_dataframe = pd.concat([test_dataframe, pd.DataFrame(additional_data)])

    result = get_last_card_total_cashback(test_dataframe, datetime(2025, 4, 1), datetime(2025, 4, 5))

    # Проверяем, что возвращается информация только по первой найденной карте
    test_result = [{'cashback': 30.0, 'last_digits': '2222', 'total_spent': 3000}, {'cashback': 30.0, 'last_digits': '2222', 'total_spent': 3000}]
    assert result == test_result


# Тест на проверку обработки пустых данных

def test_empty_data():
    empty_df = pd.DataFrame(columns=['Дата операции', 'Категория', 'Сумма операции', 'Номер карты'])

    with pytest.raises(ValueError):
        get_last_card_total_cashback(empty_df, datetime(2025, 4, 1), datetime(2025, 4, 4))

# Тест на проверку некорректных временных меток
def test_invalid_timestamps():
    test_df = pd.DataFrame({
        'Дата операции': ['01.04.2025 10:00:00', '02.04.2025 11:00:00'],
        'Категория': ['Продукты', 'Одежда'],
        'Сумма операции': [-1000, -2000],
        'Номер карты': ['4111111111111111', '4111111111111111']
    })

    # Некорректная дата окончания (раньше начала)
    with pytest.raises(ValueError):
        get_last_card_total_cashback(test_df, datetime(2025, 4, 2), datetime(2025, 4, 1))

# Тест на проверку отрицательных сумм кэшбэка
def test_negative_cashback():
    test_df = pd.DataFrame({
        'Дата операции': ['01.04.2025 10:00:00', '02.04.2025 11:00:00'],
        'Категория': ['Продукты', 'Одежда'],
        'Сумма операции': [1000, 2000],  # Положительные суммы вместо отрицательных
        'Номер карты': ['4111111111111111', '4111111111111111']
    })

    result = get_last_card_total_cashback(test_df, datetime(2025, 4, 1), datetime(2025, 4, 3))

    assert result[0]['cashback'] == pytest.approx(-30.0)  # Кэшбэк должен быть отрицательным


# Тест на проверку обработки пустых строк в номере карты
def test_empty_card_numbers():
    test_df = pd.DataFrame({
        'Дата операции': ['01.04.2025 10:00:00', '02.04.2025 11:00:00'],
        'Категория': ['Продукты', 'Одежда'],
        'Сумма операции': [-1000, -2000],
        'Номер карты': ['', '4111111111111111']
    })

    result = get_last_card_total_cashback(test_df, datetime(2025, 4, 1), datetime(2025, 4, 3))

    assert result[0]['last_digits'] == '1111'
    assert result[0]['total_spent'] == pytest.approx(2000.0)
    assert result[0]['cashback'] == pytest.approx(20.0)

# Фикстура для создания тестовых данных
@pytest.fixture
def test_settings_data():
    return {
        "username": "test_user",
        "theme": "dark",
        "language": "ru"
    }

# Тестовый набор данных для параметризованного теста
@pytest.mark.parametrize(
    "test_case, expected_result",
    [
        ("valid_json", {"username": "test_user", "theme": "dark", "language": "ru"}),
        ("invalid_json", {}),
        ("file_not_found", {}),
        ("empty_file", {})
    ]
)
def test_load_user_settings(test_case, expected_result, test_settings_data):
    with patch('builtins.open', new_callable=mock_open) as mock_file:
        if test_case == "valid_json":
            mock_file.return_value = mock_open(read_data=json.dumps(test_settings_data)).return_value
        elif test_case == "invalid_json":
            mock_file.return_value = mock_open(read_data="invalid json data").return_value
        elif test_case == "file_not_found":
            mock_file.side_effect = FileNotFoundError
        elif test_case == "empty_file":
            mock_file.return_value = mock_open(read_data="").return_value

        result = load_user_settings()
        assert result == expected_result


# Фикстура для создания тестового датафрейма
@pytest.fixture
def test_dataframe_top_transactions():
    data = {
        'Дата операции': [datetime(2025, 4, 1), datetime(2025, 4, 2), datetime(2025, 4, 3), datetime(2025, 4, 4),
                          datetime(2025, 4, 5)],
        'Сумма операции': [-100, -200, -300, -400, -500],
        'Категория': ['Еда', 'Транспорт', 'Развлечения', 'Товары', 'Услуги'],
        'Описание': ['Покупка в магазине', 'Поездка на такси', 'Кинотеатр', 'Супермаркет', 'Ремонт']
    }
    return pd.DataFrame(data)


# Тест на обработку пустого датафрейма
def test_get_top_transactions_empty_dataframe():
    empty_df = pd.DataFrame()
    # Проверяем, что функция вызывает ValueError
    with pytest.raises(ValueError) as exc_info:
        get_top_transactions(empty_df)

    # Проверяем сообщение об ошибке
    assert str(exc_info.value) == "Датафрейм не должен быть пустым"


# Тест на обработку некорректных данных
@pytest.mark.parametrize("incorrect_data", [
    {'Дата операции': 'некорректная дата', 'Сумма операции': -100, 'Категория': 'Еда', 'Описание': 'Покупка'},
    {'Дата операции': datetime(2025, 4, 1), 'Сумма операции': 'не число', 'Категория': 'Еда', 'Описание': 'Покупка'},
    {'Дата операции': datetime(2025, 4, 1), 'Сумма операции': -100, 'Категория': 123, 'Описание': 'Покупка'}
])
def test_get_top_transactions_incorrect_data(incorrect_data):
    df = pd.DataFrame([incorrect_data])
    with pytest.raises(Exception):
        get_top_transactions(df)


# Тест на проверку форматирования даты
def test_date_formatting(test_dataframe_top_transactions):
    result = get_top_transactions(test_dataframe_top_transactions)
    assert result['date'] == '2025.04.01'
    assert len(result['date'].split('.')) == 3


# Тест на проверку преобразования суммы
def test_amount_conversion(test_dataframe_top_transactions):
    result = get_top_transactions(test_dataframe_top_transactions)
    assert result['amount'] == 100  # Проверка на обратное преобразование отрицательного числа

# Фикстура для создания тестовых данных
@pytest.fixture
def mock_cbr_data():
    return {
        "Valute": {
            "USD": {"Value": 90.0},
            "EUR": {"Value": 100.0},
            "RUB": {"Value": 1.0}
        }
    }

# Фикстура для мокирования запроса
@pytest.fixture
def mock_requests(mock_cbr_data):
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_cbr_data
        mock_get.return_value = mock_response
        yield mock_get

# Параметризированный тест для проверки корректного получения курсов
@pytest.mark.parametrize("currencies, expected_result", [
    (["USD", "EUR"], [{"currency": "USD", "rate": 90.0}, {"currency": "EUR", "rate": 100.0}]),
    (["RUB"], [{"currency": "RUB", "rate": 1.0}]),
    (["USD", "JPY"], [{"currency": "USD", "rate": 90.0}]),  # JPY отсутствует в данных
    ([], [])  # Пустой список валют
])
def test_get_currency_rates(mock_requests, mock_cbr_data, currencies, expected_result):
    result = get_currency_rates(currencies)
    assert result == expected_result

# Тест для проверки обработки ошибок при получении данных
def test_get_currency_rates_error(mock_requests):
    mock_requests.side_effect = Exception("Network error")
    with pytest.raises(Exception):
        get_currency_rates(["USD"])

# Тест для проверки обработки некорректных данных
def test_get_currency_rates_invalid_data(mock_requests):
    mock_requests.return_value.json.return_value = {}
    with pytest.raises(ValueError):
        get_currency_rates(["USD"])

# Тест для проверки обработки несуществующих валют
def test_get_currency_rates_non_existent_currency(mock_requests, mock_cbr_data):
    result = get_currency_rates(["XYZ"])
    assert result == []

# Тест для проверки обработки некорректного формата данных
def test_get_currency_rates_invalid_format(mock_requests):
    mock_requests.return_value.json.return_value = "Invalid JSON"
    with pytest.raises(ValueError):
        get_currency_rates(["USD"])

# Тест для проверки обработки пустого ответа
def test_get_currency_rates_empty_response(mock_requests):
    mock_requests.return_value.json.return_value = None
    with pytest.raises(ValueError):
        get_currency_rates(["USD"])

# Фикстура для имитации ответа от Alpha Vantage API
@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "Global Quote": {
                "05. price": "150.12"
            }
        }
        mock_get.return_value = mock_response
        yield mock_get

# Тест для проверки корректной работы функции при успешном получении данных
@pytest.mark.parametrize("user_stocks, expected_result", [
    (["AAPL"], [{"stock": "AAPL", "price": 150.12}]),
    (["AMZN"], [{"stock": "AMZN", "price": 150.12}]),
])
def test_get_stock_prices_success(mock_requests_get, user_stocks, expected_result):
    result = get_stock_prices(user_stocks)
    assert result == expected_result
    mock_requests_get.assert_called()

# Тест для проверки обработки ошибки при получении данных
def test_get_stock_prices_error(mock_requests_get):
    user_stocks = ["TSLA"]
    mock_response = Mock()
    mock_response.json.return_value = {}
    mock_requests_get.return_value = mock_response
    result = get_stock_prices(user_stocks)
    assert result == []
    mock_requests_get.assert_called()