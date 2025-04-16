from pathlib import Path
from reports import spending_by_category
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

file_path = f"{BASE_DIR}\\data\\operations.xlsx"

with pd.ExcelFile(file_path) as xlsx_file:
    df = pd.read_excel(xlsx_file, sheet_name=0)
    dict_list = df.to_dict(orient="records")

spending_by_category(df, "Каршеринг")