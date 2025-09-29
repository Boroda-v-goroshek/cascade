from pathlib import Path
import yaml

from jsonargparse import CLI

from src.cascade.tables.table import TableEditor


def read_table(table_url: str, credentials_file: str):
    table_editor = TableEditor(table_url, credentials_file)
    df = table_editor.get_named_table()

    print(df)


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