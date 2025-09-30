from pathlib import Path
import yaml

from jsonargparse import CLI

from cascade.cvat.cvat_core import upload_from_share_folders
from cascade.cvat.cvat_core import get_cvat_data
from tools.parse_fsra_table import get_archive_numbers, get_archive_names_for_numbers


def main(args_path):
    if args_path:
        with open(args_path, "r", encoding="utf-8") as file:
            args = yaml.safe_load(file)
    else:
        raise ValueError("args_path is empty or invalid")
    
    path_to_cvat_yml = args["path_to_cvat_yml"]
    project_id = args["project_id"]
    start_share_path = args["start_share_path"]

    table_url = args["table_url"]
    table_credentials_path = args["table_credentials_path"]
    path_to_data = args["path_to_data"]

    numbers_in_names = get_archive_numbers(table_url, table_credentials_path)
    data_names = get_archive_names_for_numbers(numbers_in_names, path_to_data)

    credentials = get_cvat_data(path_to_cvat_yml)
    
    results = upload_from_share_folders(data_names, credentials, project_id, start_share_path)
    
    with open("upload_results.txt", "w") as f:
        for dir_name, status in results.items():
            f.write(f"{dir_name}: {status}\n")
    
    print(f"\n📄 Результаты сохранены в upload_results.txt")


if __name__ == "__main__":
    CLI(main, as_positional=False)