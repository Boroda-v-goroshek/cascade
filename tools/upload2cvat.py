from pathlib import Path
import yaml

from jsonargparse import CLI

from src.cascade.cvat.cvat_core import CvatCore


def get_data_names(path_data_names: str | None) -> list[str] | None:
    """Get directory names from txt.

    Parameters
    ---------
    path_data_names: str | None
        Path to txt
        
    Returns
    -------
    list[str]
        Names list
    """
    if path_data_names is not None:
        with open(path_data_names, "r", encoding='utf-8') as file:
            return file.readlines()
    
    return None


def download_process(cvat_credentials_path: str, project_id: int, share_path: str, path_data_names: str | None):
    """Download data to CVAT.

    Parameters
    ----------
    cvat_credentials_path: str
    project_id: int
    share_path: str
    path_data_names: str
    """
    
    cvat_core = CvatCore(cvat_credentials_path)
    data_names = get_data_names(path_data_names)
    
    if data_names is not None:
        cvat_core.upload_from_share_folders(directory_names=data_names, project_id=project_id, share_path=share_path)
    else:
        cvat_core.upload_from_share_folders_all(project_id=project_id, share_path=share_path)


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

    download_process(
        cvat_credentials_path=cvat_credentials_path,
        project_id=project_id,
        share_path=share_path,
        path_data_names=path_to_data_names
    )

if __name__ == "__main__":
    CLI(main, as_positional=False)