from pathlib import Path
import yaml
import os

from jsonargparse import CLI
import pandas as pd

from src.cascade.tables.table import TableEditor


def get_archive_names(table_url: str, credentials_file: str, path_to_archives: str) -> list[str]:
    table_editor = TableEditor(table_url, credentials_file)
    df = table_editor.get_named_table()
    
    required_columns = ['Подходит с разметкой боксов', 'Номер папки']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"В таблице отсутствуют необходимые столбцы: {missing_columns}")
    
    filtered_df = df[df['Подходит с разметкой боксов'] == 1]
    archive_number_in_names = filtered_df['Номер папки'].astype(str).tolist()
    
    if not os.path.exists(path_to_archives):
        raise FileNotFoundError(f"Путь к архивам не существует: {path_to_archives}")
    
    archive_names = []
    
    for filename in os.listdir(path_to_archives):
        file_path = os.path.join(path_to_archives, filename)
        
        if os.path.isfile(file_path):
            name_without_ext = os.path.splitext(filename)[0]
            name_parts = name_without_ext.split('_')
            
            if name_parts[0] in archive_number_in_names:
                archive_names.append(filename)
    
    return archive_names


def read_table(table_url: str, credentials_file: str):
    table_editor = TableEditor(table_url, credentials_file)
    df = table_editor.get_named_table()


def main(args_path: Path | str):
    """Main function."""
    if args_path:
        with open(args_path, "r", encoding="utf-8") as file:
            args = yaml.safe_load(file)
    else:
        raise ValueError("args_path is empty or invalid")

    table_url = args["table_url"]
    credentials_path = args["credentials_path"]
    
    read_table(table_url, credentials_path)


if __name__ == "__main__":
    CLI(main, as_positional=False)