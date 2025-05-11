from typing import Optional

import pandas as pd

from src.decorators import export_to_file


@export_to_file
def spending_by_category(
    transactions: pd.DataFrame, category: str, date: Optional[str] = None
) -> int | float | pd.DataFrame:
    """
    Функция для получения суммы трат по определённой категории за последние 3 месяца.

    Параметры:
    transactions (pd.DataFrame): датафрейм с транзакциями, содержащий столбцы «Дата операции»,
    «Категория» и «Сумма операции».
    category (str): название категории, по которой нужно подсчитать траты.
    date (str, optional): дата для расчёта периода в формате «dd.mm.yyyy HH:MM:SS».
    Если не указана, используется текущая дата.

    Возвращает:
    int | float: сумма трат по указанной категории за последние 3 месяца.

    Описание:
    Функция определяет границы периода (последние 3 месяца от указанной даты или текущей даты),
    фильтрует транзакции по категории и периоду, затем возвращает сумму трат по отфильтрованным транзакциям.
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
    filtered_df = filtered_df[(filtered_df["Сумма операции"] < 0)]
    # Возвращаем сумму трат по отфильтрованным транзакциям
    return filtered_df
