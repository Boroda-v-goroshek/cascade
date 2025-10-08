from pathlib import Path
import yaml

from jsonargparse import CLI

from src.cascade.cvat.cvat_core import CvatDownloader


def get_tasks_ids(path_to_tasks_ids: str | Path | None) -> list[int] | None:
    """Get tasks ids from txt.

    Parameters
    ---------
    path_to_tasks_ids: str | Path | None
        Path to txt
        
    Returns
    -------
    list[str]
        Ids list
    """
    if path_to_tasks_ids is not None:
        try:
            with open(path_to_tasks_ids, "r", encoding='utf-8') as file:
                tasks_ids = file.readlines()
            
            formated_tasks_ids = []
            for task_id in tasks_ids:
                if task_id[-1] == '\n':
                    task_id = task_id[:-1]
                formated_tasks_ids.append(int(task_id))
            return formated_tasks_ids
        except Exception as e:
            raise e
    
    return None


def process_of_download(
        cvat_credentials_path: str, 
        project_id: int, 
        path_to_tasks_ids: str | None,
        output_dir: str = "./exports",
        export_format : str = "YOLO 1.1",
        include_images: bool = False,
        table_url: str | None = None,
        sheet_id: int | None = None,
        table_credentials_path: str | None = None,
        column_names: list[str] | None = None        
    ):    
    cvat_downloader = CvatDownloader(
        cvat_credentials_path
    )
    tasks_ids = get_tasks_ids(path_to_tasks_ids)
    cvat_downloader.export_tasks(
        project_id=project_id,
        export_format=export_format,
        task_ids=tasks_ids,
        output_dir=output_dir,
        include_images=include_images
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
    path_to_tasks_ids = args["path_to_tasks_ids"]
    export_format = args["export_format"]
    output_dir = args["output_dir"]
    #include_images = args["include_images"]
    table_url = args["table_url"]
    sheet_id = args["sheet_id"]
    table_credentials_path = args["table_credentials_path"]
    column_names = args["column_names"]

    process_of_download(
        cvat_credentials_path=cvat_credentials_path,
        project_id=project_id,
        path_to_tasks_ids=path_to_tasks_ids,
        output_dir=output_dir,
        export_format=export_format,
        table_url=table_url,
        sheet_id=sheet_id,
        table_credentials_path=table_credentials_path,
        column_names=column_names
    )

if __name__ == "__main__":
    CLI(main, as_positional=False)