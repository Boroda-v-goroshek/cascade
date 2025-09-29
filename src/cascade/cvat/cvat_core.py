import yaml

from pathlib import Path
from cvat_sdk import make_client
from cvat_sdk.core.proxies.tasks import ResourceType


def get_cvat_data(path_to_yml: str) -> tuple[str, str, str, str]:
    if path_to_yml:
        with open(path_to_yml, "r", encoding="utf-8") as file:
            args = yaml.safe_load(file)
        
    server_url = args["server_url"]
    username = args["username"]
    password = args["password"]
    project_name = args["project_name"]

    return server_url, username, password, project_name


def upload_archives_to_cvat(
    server_url: str,
    username: str,
    password: str,
    project_name: str,
    archive_names: list[str],
    archives_dir: Path | str
):
    """Download data to CVAT like once job.
    
    Parameters
    ---------
    server_url: str
        URL for CVAT server
    username: str
        Login of user in CVAT
    password: str
        Password of user in CVAT
    project_name: str
        Target project
    archive_names: list[str]
        List of target archive names
    archives_dir: Path | str
        Path to directory with archives
    """
    
    with make_client(server_url, credentials=(username, password)) as client:
        projects = client.projects.list()
        target_project = None
        
        for project in projects:
            if project.name == project_name:
                target_project = project
                break
        
        if target_project is None:
            raise ValueError(f"Project '{project_name}' does not exist!")
        
        print(f"Find: {project_name} (ID: {target_project.id})")

        archives_dir = Path(archives_dir) if isinstance(archives_dir, str) else archives_dir
        
        for archive_name in archive_names:
            archive_path = archives_dir / archive_name
            
            if not archive_path.exists():
                print(f"WARNING: archive {archive_path} does not exist! Skipped this")
                continue
            
            task_name = Path(archive_name).stem
            
            try:
                print(f"Task is creating: {task_name}")

                task_spec = {
                    'name': task_name,
                    'project_id': target_project.id,
                }
                
                task = client.tasks.create(task_spec)
                
                task.upload_data(
                    resources=[str(archive_path)],
                    resource_type=ResourceType.LOCAL
                )
                
                print(f"Успешно создана задача '{task_name}' (ID: {task.id})")
                
            except Exception as e:
                print(f"Ошибка при создании задачи {task_name}: {e}")
