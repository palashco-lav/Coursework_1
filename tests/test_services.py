from unittest.mock import patch

import pytest

# Импортируем тестируемый модуль
from src.services import investment_bank, logger_utils, round_to


# Фикстура для генерации тестовых транзакций
@pytest.fixture
def transactions() -> list:
    return [
        {"Дата операции": "01.04.2025 00:00:01", "Сумма операции": 123.45},
        {"Дата операции": "15.04.2025 00:00:01", "Сумма операции": 567.89},
        {"Дата операции": "01.04.2025 00:00:01", "Сумма операции": 987.65},
    ]


# Тестирование функции round_to
@pytest.mark.parametrize("number,base,expected", [(123.45, 10, 130), (567.89, 50, 600), (987.65, 100, 1000)])
def test_round_to(number: int | float, base: int, expected: int) -> None:
    result = round_to(number, base)
    assert result == expected


# Тестирование обработки ошибок в round_to
def test_round_to_errors() -> None:
    with pytest.raises(TypeError):
        round_to("строка", 10)

    with pytest.raises(ValueError):
        round_to(123.45, -10)

    with pytest.raises(ValueError):
        round_to(123.45, 0)


# Тестирование функции investment_bank
@pytest.mark.parametrize(
    "month,limit,expected", [("2025-04", 10, 11.01), ("2025-04", 50, 71.01), ("2025-04", 100, 121.01)]
)
def test_investment_bank(transactions: list, month: str, limit: int, expected: float) -> None:
    result = investment_bank(month, transactions, limit)
    assert result == expected


# Тестирование обработки ошибок в investment_bank
def test_investment_bank_errors() -> None:
    with pytest.raises(ValueError):
        investment_bank("неверный_формат", [], 10)

    with pytest.raises(ValueError):
        investment_bank("2025-04", [{"Дата операции": "неверный_формат", "Сумма операции": 123.45}], 10)


# Тестирование логгирования
def test_logging() -> None:
    with patch.object(logger_utils, "debug") as mock_debug:
        round_to(123.45, 10)
        mock_debug.assert_called()

    with patch.object(logger_utils, "error") as mock_error:
        try:
            round_to("строка", 10)
        except TypeError:
            pass
        mock_error.assert_called()
