import pandas as pd
import pytest
from datetime import datetime
from unittest.mock import patch
from src.reports import spending_by_category

# Фикстура для создания тестового датафрейма
@pytest.fixture
def transactions_df():
    data = {
        'Дата операции': ['01.01.2025 00:00:00', '01.02.2025 00:00:00', '01.03.2025 00:00:00', '01.04.2025 00:00:00'],
        'Категория': ['Еда', 'Еда', 'Развлечения', 'Еда'],
        'Сумма операции': [100, 200, 150, 300]
    }
    return pd.DataFrame(data)

# Тест на корректное вычисление суммы за 3 месяца
@pytest.mark.parametrize("category, expected_sum", [
    ("Еда", 600),  # Все транзакции за 3 месяца
    ("Развлечения", 150),  # Одна транзакция
    ("Транспорт", 0)  # Нет транзакций
])
def test_spending_by_category(transactions_df, category, expected_sum):
    with patch('pandas._libs.tslibs.timestamps.Timestamp.now') as mock_datetime:
        mock_datetime.return_value = pd.Timestamp('2025-04-01')
        result = spending_by_category(transactions_df, category)
        assert result == expected_sum

# Тест на обработку пустого датафрейма
def test_empty_dataframe():
    empty_df = pd.DataFrame()
    result = spending_by_category(empty_df, 'Еда')
    assert result == 0

# Тест на проверку отсутствия необходимых столбцов
def test_missing_columns(transactions_df):
    transactions_df = transactions_df.drop(columns=['Категория'])
    with pytest.raises(ValueError):
        spending_by_category(transactions_df, 'Еда')

# Тест на проверку некорректной даты
def test_invalid_date_format(transactions_df):
    with pytest.raises(ValueError):
        spending_by_category(transactions_df, 'Еда', '2025-04-24')

# Тест на проверку корректной работы с указанной датой
def test_with_specified_date(transactions_df):
    date_str = '01.04.2025 00:00:00'
    result = spending_by_category(transactions_df, 'Еда', date_str)
    assert result == 300  # Только последняя транзакция попадает в период

# Тест на проверку корректной работы с разными временными периодами
@pytest.mark.parametrize("date_str, expected_sum", [
    ('01.03.2025 00:00:00', 300),  # Период с декабря по февраль
    ('01.02.2025 00:00:00', 500),  # Период с ноября по январь
])
def test_different_periods(transactions_df, date_str, expected_sum):
    result = spending_by_category(transactions_df, 'Еда', date_str)
    assert result == expected_sum