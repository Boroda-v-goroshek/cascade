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


def test_cvat_connection(server_url: str, server_port:int, username: str, password: str):
    """
    Проверяет подключение к CVAT и выводит базовую информацию
    """
    try:
        print(f"Пытаюсь подключиться к {server_url}...")
        
        with make_client(host=server_url, port=server_port, credentials=(username, password)) as client:
            print("✓ Успешное подключение!")
            
            # Проверяем список проектов
            projects = client.projects.list()
            print(f"✓ Найдено проектов: {len(projects)}")
            
            # Выводим названия проектов
            if projects:
                print("Список проектов:")
                for project in projects:
                    print(f"  - {project.name} (ID: {project.id})")
            else:
                print("  Проекты не найдены")
            
            # Проверяем список задач
            tasks = client.tasks.list()
            print(f"✓ Найдено задач: {len(tasks)}")
            
            return True
            
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        return False
    

import requests
from urllib.parse import urljoin

def find_cvat_endpoints(server_url: str, username: str, password: str):
    print(f"Поиск рабочих endpoints CVAT на {server_url}...")
    
    # Возможные endpoints для разных версий CVAT
    endpoints_to_try = [
        "/api/auth/whoami",
        "/auth/whoami", 
        "/api/v1/auth/whoami",
        "/api/v1/users/self",
        "/api/users/self",
        "/api/server/about",
        "/api/about",
        "/api/projects",
        "/api/v1/projects",
        "/api/tasks", 
        "/api/v1/tasks"
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_try:
        full_url = urljoin(server_url, endpoint)
        try:
            response = requests.get(full_url, auth=(username, password), timeout=10)
            if response.status_code == 200:
                print(f"✓ РАБОТАЕТ: {endpoint}")
                working_endpoints.append(endpoint)
            else:
                print(f"✗ {endpoint} - HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint} - ошибка: {e}")
    
    return working_endpoints

# Проверим какие endpoints работают
# working = find_cvat_endpoints("http://212.20.47.88:7555", "Boroda-v-goroshek", "RAlf2005")
# print(f"\nРабочие endpoints: {working}")


if __name__ == "__main__":
    # Замените на ваши данные
    CVAT_SERVER_URL = "http://212.20.47.88"
    CVAT_SERVER_PORT = 7555
    USERNAME = "Boroda-v-goroshek"
    PASSWORD = "RAlf2005"
    
    test_cvat_connection(CVAT_SERVER_URL, CVAT_SERVER_PORT, USERNAME, PASSWORD)
