from pathlib import Path
from reports import spending_by_category
import pandas as pd
import src.views as views



BASE_DIR = Path(__file__).resolve().parent.parent
file_path = f"{BASE_DIR}\\data\\operations.xlsx"

with pd.ExcelFile(file_path) as xlsx_file:
    df = pd.read_excel(xlsx_file, sheet_name=0)
    dict_list = df.to_dict(orient="records")



views.function_for_home_page("2018-12-12 00:00:00")# "%Y-%m-%d %H:%M:%S")

spending_by_category(df, "Каршеринг", "31.12.2021 16:44:00")