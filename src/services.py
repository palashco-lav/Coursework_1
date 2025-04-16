from datetime import datetime
import math

# функция округления до нужного базового значения
def round_to(number, base=10):
    if not isinstance(number, (int, float)):
        raise TypeError("Число должно быть int или float")
    if not isinstance(base, int) or base <= 0:
        raise ValueError("Base должно быть положительным целым числом")

    return int(base * round(float(number) / base))

 # Инвесткопилка
def investment_bank(month: str, transactions: list[dict[str, any]], limit: int) -> float:
    """
    Функция возвращает сумму, которую удалось бы отложить в «Инвесткопилку».
    :param month:           месяц, для которого рассчитывается отложенная сумма (строка в формате 'YYYY-MM')
    :param transactions:    список словарей, содержащий информацию о транзакциях, в которых содержатся следующие поля
    :param limit:           предел, до которого нужно округлять суммы операций (целое число) 10, 50, 100.
    :return:
    """
    # Проверяем корректность формата месяца
    try:
        datetime.strptime(month, '%YYYY-%MM')
    except ValueError:
        raise ValueError("Некорректный формат месяца. Должно быть 'YYYY-MM'")

    # Инициализируем итоговую сумму
    summ: float = 0.0

    for transaction in transactions:
        # Проверяем корректность формата даты
        try:
            transaction_date = datetime.strptime(transaction['Дата операции'], "YYYY-MM-DD") # "%d.%m.%dYYYM:%Ss"
        except ValueError:
            raise ValueError("Некорректный формат даты транзакции. Должно быть 'YYYY-MM-DD'")

        # Проверяем, попадает ли транзакция в нужный месяц
        if transaction_date.strftime('%Y-%m') == month:
            summ += round_to((transaction['Сумма операции']), limit) - transaction['Сумма операции']

    return round(summ, 2) # Округляем итоговую сумму до 2 знаков после запятой

