import pytest
from src.services import round_to, investment_bank
from unittest.mock import patch, Mock

# Фикстура для создания тестовых данных
@pytest.fixture
def test_data():
    return [
        (123.45, 10, 120),
        (123.45, 5, 125),
        (123.45, 1, 123),
        (123.45, 20, 120),
        (123.45, 25, 125)
    ]

# Тестовый кейс для проверки корректной работы функции
@pytest.mark.parametrize("number, base, expected", [
    (123.45, 10, 120),
    (123.45, 5, 125),
    (123.45, 1, 123),
    (123.45, 20, 120),
    (123.45, 25, 125)
])
def test_round_to_success(number, base, expected):
    result = round_to(number, base)
    assert result == expected

# Тестовый кейс для проверки обработки ошибок (некорректный тип числа)
@pytest.mark.parametrize("number, base", [
    ("строка", 10),
    ([1, 2, 3], 10),
    ({"key": "value"}, 10),
    (True, 10)
])
def test_round_to_type_error(number, base):
    with pytest.raises(TypeError) as exc_info:
        round_to(number, base)
    assert str(exc_info.value) == "Число должно быть int или float"

# Фикстура для создания тестовых транзакций
@pytest.fixture
def test_transactions():
    return [
        {
            "Дата операции": "2025-04-01",
            "Сумма операции": 123.45
        },
        {
            "Дата операции": "2025-04-02",
            "Сумма операции": 456.78
        },
        {
            "Дата операции": "2025-03-31",
            "Сумма операции": 789.01
        }
    ]

# Тестовый кейс для проверки корректной работы функции
@pytest.mark.parametrize("month, limit, expected", [
    ("2025-04", 10, 12.27),
    ("2025-04", 50, 23.27),
    ("2025-04", 100, 33.27)
])
def test_investment_bank_success(test_transactions, month, limit, expected):
    with patch('__main__.round_to') as mock_round_to:
        mock_round_to.side_effect = lambda x, y: x + (y - x % y)
        result = investment_bank(month, test_transactions, limit)
        assert result == expected

# Тестовый кейс для проверки обработки ошибок (некорректный формат месяца)
@pytest.mark.parametrize("month, transactions, limit", [
    ("2025-13", test_transactions, 10),
    ("2025-00", test_transactions, 50),
    ("2025-", test_transactions, 100),
    ("2025", test_transactions, 10)
])
def test_investment_bank_month_format_error(month, transactions, limit):
    with pytest.raises(ValueError) as exc_info:
        investment_bank(month, transactions, limit)
    assert str(exc_info.value) == "Некорректный формат месяца. Должно быть 'YYYY-MM'"

# Тестовый кейс для проверки обработки ошибок (некорректный формат даты транзакции)
@pytest.mark.parametrize("month, transactions, limit", [
    ("2025-04", [{'Дата операции': '2025-04', 'Сумма операции': 100}], 10),
    ("2025-04", [{'Дата операции': '2025-04-32', 'Сумма операции': 100}], 50),
    ("2025-04", [{'Дата операции': '2025-04-01T12:00', 'Сумма операции': 100}], 100)
])
def test_investment_bank_transaction_date_error(month, transactions, limit):
    with pytest.raises(ValueError) as exc_info:
        investment_bank(month, transactions, limit)
    assert str(exc_info.value) == "Некорректный формат даты транзакции. Должно быть 'YYYY-MM-DD'"

# Тестовый кейс для проверки обработки ошибок (некорректное значение limit)
@pytest.mark.parametrize("month, transactions, limit", [
    ("2025-04", test_transactions, 5),
    ("2025-04", test_transactions, 25),
    ("2025-04", test_transactions, 150)
])
def test_investment_bank_limit_error(month, transactions, limit):
    with pytest.raises(ValueError) as exc_info:
        investment_bank(month, transactions, limit)
    assert str(exc_info.value) == "Limit должен быть 10, 50 или 100"

# Тестовый кейс для проверки работы с пустыми данными
def test_investment_bank_empty_transactions():
    result = investment_bank("2025-04", [], 10)
    assert result == 0.0