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
    

    def get_sheet_count(self) -> int:
        return len(self.sheet.worksheets())


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

    def write_data_to_table(self, data_dict: dict, worksheet_name: int = 0):
        """
        Add data to table for target columns.
        
        Parameters
        ----------
        data_dict : dict
            Example: {'column name': 'value', ...}
        worksheet_name : int
            Sheet id in target table
        """
        worksheet = self.sheet.get_worksheet(worksheet_name)
        
        try:
            all_data = worksheet.get_all_values()
            
            if not all_data:
                raise ValueError("Table is empty!")
            
            headers = all_data[0]
            
            new_row = [""] * len(headers)
            
            for column_name, value in data_dict.items():
                if column_name in headers:
                    column_index = headers.index(column_name)
                    new_row[column_index] = str(value) if value is not None else ""
                else:
                    print(f"⚠️ Column'{column_name}' does not find! Excists columns: {headers}")
            
            worksheet.append_row(new_row)
            
            print(f"✅ Succes added data:")
            for column_name, value in data_dict.items():
                if column_name in headers:
                    print(f"   📌 {column_name}: {value}")
            
        except Exception as e:
            print(f"❌ Add data error: {e}")