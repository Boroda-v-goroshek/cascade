from pathlib import Path
import yaml

from jsonargparse import CLI

from src.cascade.cvat.cvat_core import CvatUploader


def get_data_names(path_data_names: str | Path | None) -> list[str] | None:
    """Get directory names from txt.

    Parameters
    ---------
    path_data_names: str | Path | None
        Path to txt
        
    Returns
    -------
    list[str]
        Names list
    """
    if path_data_names is not None:
        try:
            with open(path_data_names, "r", encoding='utf-8') as file:
                return file.readlines()
        except Exception as e:
            raise e
    
    return None


def process_of_upload(
        cvat_credentials_path: str, 
        project_id: int, 
        share_path: str, 
        path_data_names: str | None,
        table_url: str | None = None,
        sheet_id: int | None = None,
        table_credentials_path: str | None = None,
        column_names: list[str] | None = None        
    ):
    """Upload data to CVAT.

    Parameters
    ----------
    cvat_credentials_path: str
        Path to cvat private data (url, username, password)
    project_id: int
        Number (ID) of target project
    share_path: str
        Path on /mnt/cvat_share/
    path_data_names: str | None
        Path to .txt-file with directory names you need
    table_url: str | None
        Url of target table for writing data
    sheet_id: int | None
        Id of sheet in target table
    table_credentials_path: str | None
        Path to privat data for table
    column_names: list[str] | None
        Target columns names
    """
    
    cvat_uploader = CvatUploader(
        cvat_credentials_path, 
        table_url=table_url, 
        table_credentials_path=table_credentials_path
    )
    data_names = get_data_names(path_data_names)
    cvat_uploader.upload_from_share_folders(
        directory_names=data_names, 
        project_id=project_id, 
        share_path=share_path,
        column_names=column_names,
        sheet_id=sheet_id
    )


def main(args_path: str | Path):
    """Main function."""
    if args_path:
        with open(args_path, "r", encoding="utf-8") as file:
            args = yaml.safe_load(file)
    else:
        raise ValueError("args_path is empty or invalid")
    
    cvat_credentials_path = args["cvat_credentials_path"]
    project_id = args["project_id"]
    share_path = args["share_path"]
    path_to_data_names = args["path_to_data_names"]
    table_url = args["table_url"]
    sheet_id = args["sheet_id"]
    table_credentials_path = args["table_credentials_path"]
    column_names = args["column_names"]

    process_of_upload(
        cvat_credentials_path=cvat_credentials_path,
        project_id=project_id,
        share_path=share_path,
        path_data_names=path_to_data_names,
        table_url=table_url,
        sheet_id=sheet_id,
        table_credentials_path=table_credentials_path,
        column_names=column_names
    )

if __name__ == "__main__":
    CLI(main, as_positional=False)