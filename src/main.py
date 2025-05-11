from pathlib import Path

import pandas as pd
import src.views as views
import src.services as services
import src.reports as reports


BASE_DIR = Path(__file__).resolve().parent.parent
file_path = f"{BASE_DIR}/data/operations.xlsx"

with pd.ExcelFile(file_path) as xlsx_file:
    df = pd.read_excel(xlsx_file, sheet_name=0)
    dict_list = df.to_dict(orient="records")


answer_1 = views.function_for_home_page("2018-12-12 00:00:00")
# read_data["Дата операции"] = pd.to_datetime(read_data["Дата операции"], format="%d.%m.%Y %H:%M:%S")

answer_2 = services.investment_bank("2021-12", df.to_dict(orient="records"), 100)

answer_3 = reports.spending_by_category(df, "Супермаркеты", "25.08.2021 23:59:59")
