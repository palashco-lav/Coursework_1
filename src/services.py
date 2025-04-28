from datetime import datetime
import logging
from pathlib import Path

logger_utils = logging.getLogger(__name__)
logger_utils.setLevel(logging.DEBUG)

# настройка обработчика и форматировщика для logger_masks
handler_utils = logging.FileHandler(
    f"{Path(__file__).resolve().parent.parent}\\services.log", mode="w", encoding="utf-8"
)
formatter_utils = logging.Formatter("%(asctime)s %(filename)s %(levelname)s: %(message)s")

# добавление форматировщика к обработчику
handler_utils.setFormatter(formatter_utils)
# добавление обработчика к логгеру
logger_utils.addHandler(handler_utils)

# функция округления до нужного базового значения
def round_to(number, base=10):
    logger_utils.debug(f"Округляю число {number} до базового значения {base}")
    if not isinstance(number, (int, float)) or isinstance(number, bool):
        logger_utils.error("Число должно быть int или float")
        raise TypeError("Число должно быть int или float")

    if not isinstance(base, int) or base <= 0:
        logger_utils.error("Base должно быть положительным целым числом")
        raise ValueError("Base должно быть положительным целым числом")

    result = int(base * round(float(number) / base))
    logger_utils.debug(f"Округлённое число {result}")
    return result

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
        datetime.strptime(month, '%Y-%m')
    except ValueError:
        logger_utils.error("Некорректный формат месяца. Должно быть 'YYYY-MM'")
        raise ValueError("Некорректный формат месяца. Должно быть 'YYYY-MM'")
    logger_utils.debug(f"Запуск функции определения потенциала инвесткопилки"
                       f"Расчетный месяц {datetime.strftime('%m')}"
                       f"Предел округления {limit}")
    # Инициализируем итоговую сумму
    summ: float = 0.0

    for transaction in transactions:
        # Проверяем корректность формата даты
        try:
            transaction_date = datetime.strptime(transaction['Дата операции'], "%Y-%m-%d") # "%d.%m.%dYYYM:%Ss"
        except ValueError:
            logger_utils.error("Некорректный формат даты транзакции. Должно быть 'YYYY-MM-DD'")
            raise ValueError("Некорректный формат даты транзакции. Должно быть 'YYYY-MM-DD'")

        # Проверяем, попадает ли транзакция в нужный месяц
        if transaction_date.strftime('%Y-%m') == month:
            summ += round_to((transaction['Сумма операции']), limit) - transaction['Сумма операции']

    return round(summ, 2) # Округляем итоговую сумму до 2 знаков после запятой




