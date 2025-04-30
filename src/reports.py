from typing import Optional

import pandas as pd


def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> int | float:
    # transactions_df, category_name: str, date=None):
    """
    Функция для получения трат по категории за последние 3 месяца

    Параметры:
    transactions_df (pd.DataFrame) - датафрейм с транзакциями
    category_name (str) - название категории
    date (datetime, optional) - дата для расчета периода (по умолчанию текущая дата)

    Возвращает:
    сумма трат по категории за последние 3 месяца
    """

    # Если дата не передана, используем текущую дату
    if date is None:
        # date_dt = pd.Timestamp.now()
        # date_dt = date_dt.normalize()
        date_dt = pd.Timestamp.now().normalize()
        # Определяем границы периода (3 месяца назад от указанной даты)
        start_date = date_dt - pd.DateOffset(months=3)
        # date_dt = pd.to_datetime(date, '%dd.%MM.%YYYY %HH:%MM:%SS')
    else:
        # Определяем границы периода (3 месяца вперёд от указанной даты)
        start_date = pd.to_datetime(date, format="%d.%m.%Y %H:%M:%S")
        date_dt = start_date + pd.DateOffset(months=3)

    # Проверяем, что датафрейм не пустой
    if transactions.empty:
        # data_out = dict(category=category, amound=0)
        # result = json.dumps(data_out, ensure_ascii=False)
        return 0  # pd.DataFrame(result)

    # Проверяем наличие необходимых столбцов
    required_columns = ["Дата операции", "Категория", "Сумма операции"]
    if not set(required_columns).issubset(transactions.columns):
        raise ValueError("Датафрейм должен содержать столбцы: Дата операции, Категория, Сумма операции")

    # Преобразуем столбец date в формат datetime, если это еще не сделано
    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    # Фильтруем транзакции по категории и периоду
    transactions = transactions[(transactions["Дата операции"] >= start_date)]
    transactions = transactions[(transactions["Дата операции"] <= date_dt)]
    filtered_df = transactions[(transactions["Категория"] == category)]

    # Возвращаем сумму трат по отфильтрованным транзакциям
    return filtered_df["Сумма операции"].sum()
