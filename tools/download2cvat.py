from pathlib import Path
import yaml

from jsonargparse import CLI

from cascade.cvat.cvat_core import upload_archives_to_cvat
from cascade.cvat.cvat_core import get_cvat_data
from cascade.tables.table import TableEditor
from tools.test_table import get_archive_names


def main(args_path: Path | str):
    """Main function."""

    if args_path:
        with open(args_path, "r", encoding="utf-8") as file:
            args = yaml.safe_load(file)
    else:
        raise ValueError("args_path is empty or invalid")

    path_to_cvat_yml = args["path_to_cvat_yml"]
    archives_dir = args["archives_dir"]
    table_url = args["table_url"]
    table_cred_file = args["table_cred_file"]

    server_url, username, password, project_name = get_cvat_data(path_to_cvat_yml)
    archive_names = get_archive_names(table_url, table_cred_file)

    upload_archives_to_cvat(
        server_url=server_url,
        username=username,
        password=password,
        project_name=project_name,
        archive_names=archive_names,
        archives_dir=archives_dir
    )


if __name__ == "__main__":
    CLI(main, as_positional=False)