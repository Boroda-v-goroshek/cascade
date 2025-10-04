import json
import os
from typing import Any
from typing import cast

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]


class TableEditor():
    def __init__(self, url: str, credentials_file: str):
        self.creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        self.gc = gspread.authorize(self.creds)
        self.sheet = self.gc.open_by_url(url)


    def get_named_table(self, worksheet_name: int = 0) -> pd.DataFrame:
        worksheet = self.sheet.get_worksheet(worksheet_name)
    
        try:
            all_data = worksheet.get_all_values()
            
            if not all_data or len(all_data) < 2:
                print("⚠️ На листе недостаточно данных для таблицы")
                return pd.DataFrame()
            
            headers = all_data[0]
            rows = all_data[1:]
            
            non_empty_rows = [row for row in rows if any(cell.strip() for cell in row)]
            
            df = pd.DataFrame(non_empty_rows, columns=headers)
            print(f"✅ Загружено данных: {len(df)} строк, {len(df.columns)} столбцов")
            return df
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return pd.DataFrame()


    def append_to_end(self, data: pd.DataFrame | list, worksheet_name: int=0):
        """Append data into the end of table.
        
        Parameters
        ----------
        data: DataFrame | list
            Pandas dataframe or list of lists
        worksheet_name: int
            Index of sheet
        """
        worksheet = self.sheet.get_worksheet(worksheet_name)
        
        if isinstance(data, pd.DataFrame):
            values = data.values.tolist()
        else:
            values = data
        
        worksheet.append_rows(values)
        print(f"✅ Добавлено {len(values)} строк в конец листа '{worksheet.title}'")
        
    def append_to_range(self, data: pd.DataFrame | list, range_str: str, worksheet_name: int = 0):
        """
        Добавить данные в определенный диапазон
        
        Parameters
        ----------
        data: DataFrame | list
            Данные для записи (должны соответствовать размеру диапазона)
        range_str: str
            Диапазон в формате 'A1:B10', 'G2:G197' и т.д.
        worksheet_name: int
            Индекс листа
        """
        worksheet = self.sheet.get_worksheet(worksheet_name)
        
        try:
            if isinstance(data, pd.DataFrame):
                values = data.values.tolist()
            else:
                values = data
            
            if values and not isinstance(values[0], list):
                values = [[item] for item in values]
            
            worksheet.update(range_str, values)
            
            print(f"✅ Данные записаны в диапазон '{range_str}' на листе '{worksheet.title}'")
            print(f"📊 Записано {len(values)} значений")
            
        except Exception as e:
            print(f"❌ Ошибка записи в диапазон: {e}")