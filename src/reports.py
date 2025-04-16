import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional


def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
        # transactions_df, category_name: str, date=None):
    """
    Функция для получения трат по категории за последние 3 месяца

    Параметры:
    transactions_df (pd.DataFrame) - датафрейм с транзакциями
    category_name (str) - название категории
    date (datetime, optional) - дата для расчета периода (по умолчанию текущая дата)

    Возвращает:
    float - сумма трат по категории за последние 3 месяца
    """

    # Если дата не передана, используем текущую дату
    date_dt = datetime.now()
    if date is not None:
        date_dt = datetime.strptime(date, '%dd.%MM.%YYYY %HH:%MM:%SS')

    # Проверяем, что датафрейм не пустой
    if transactions.empty:
        return 0.0

    transactions_data = transactions.to_dict(orient='records')

    # Проверяем наличие необходимых столбцов
    required_columns = ['Дата операции', 'Категория', 'Сумма операции']
    if not set(required_columns).issubset(transactions.columns):
        raise ValueError("Датафрейм должен содержать столбцы: Дата операции, Категория, Сумма операции")

    sum = 0

    for transaction in transactions_data:
        # Преобразуем столбец date в формат datetime, если это еще не сделано
        # transactions_data['Дата операции'] = pd.to_datetime(transactions_data['Дата операции'])
        transactions_time = datetime.strptime(transaction['Дата операции'], '%d.%M.%Y %H:%M:%S')

        # Определяем границы периода (3 месяца назад от указанной даты)
        start_date = date_dt - timedelta(days=90)

        # Фильтруем транзакции п    о категории и периоду
        filtered_df = transactions_data[(transactions_data['Дата операции'] >= start_date) &
                                      (transactions_data['Дата операции'] <= date_dt) &
                                      (transactions_data['Категория'] == category)]

        # Возвращаем сумму трат по отфильтрованным транзакциям
        sum += filtered_df['amount'].sum()

    return sum