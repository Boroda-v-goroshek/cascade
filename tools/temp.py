import time
from typing import Optional

import requests
import yaml
import pandas as pd


def create_session(base_url, username, password) -> requests.Session:
        """
        Create authenticated session with CVAT.

        Returns
        -------
        requests.Session
            Authenticated session
        """

        session = requests.Session()
        
        login_response = session.post(
            f"{base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=30,
        )

        if login_response.status_code != 200:
            raise Exception(f"Login failed: {login_response.text}")

        auth_data = login_response.json()
        session.headers.update({"Authorization": f"Token {auth_data['key']}"})
        
        return session


def get_all_tasks(session, base_url, project_id: int | None = None):
    """Получить все задачи (с пагинацией)"""
    all_tasks = []
    page = 1
    
    while True:
        url = f"{base_url}/api/tasks"
        params = {"page": page, "page_size": 100}
        
        if project_id:
            params["project_id"] = project_id
            
        response = session.get(url, params=params)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        
        # Современный CVAT API (с пагинацией)
        if isinstance(data, dict) and 'results' in data:
            tasks = data['results']
            all_tasks.extend(tasks)
            
            # Если нет следующей страницы - выходим
            if not data.get('next'):
                break
        # Старый CVAT API (просто список)
        elif isinstance(data, list):
            all_tasks.extend(data)
            break
        else:
            break
            
        page += 1
    
    return all_tasks


def refresh_tasks(project_id: int = 35):
    """Принудительно обновить задачи проекта с учетом пагинации"""
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    session = create_session(base_url, username, password)
    
    all_tasks = []
    page = 1
    page_size = 100  # Максимальный размер страницы
    
    # Получаем все задачи с пагинацией
    while True:
        tasks_response = session.get(
            f"{base_url}/api/tasks?project_id={project_id}&page={page}&page_size={page_size}"
        )
        
        if tasks_response.status_code != 200:
            print(f"❌ Error getting tasks: {tasks_response.status_code}")
            break
            
        tasks_data = tasks_response.json()
        
        # Проверяем разные форматы ответа
        if isinstance(tasks_data, dict) and 'results' in tasks_data:
            tasks = tasks_data['results']
            all_tasks.extend(tasks)
            
            # Проверяем есть ли следующая страница
            if not tasks_data.get('next'):
                break
        elif isinstance(tasks_data, list):
            all_tasks.extend(tasks_data)
            break  # Если вернулся список, значит это все задачи
        else:
            print(f"⚠ Unexpected response format: {type(tasks_data)}")
            break
            
        page += 1
    
    print(f"Total tasks found: {len(all_tasks)}")
    
    for task in all_tasks:
        task_id = task['id']
        task_name = task['name']
        
        print(f"Refreshing task: {task_name} (ID: {task_id})")
        
        # Попробовать обновить данные задачи
        update_response = session.patch(
            f"{base_url}/api/tasks/{task_id}",
            json={"name": task_name}
        )
        print(f"   Update status: {update_response.status_code}")

def diagnose_task_problems(session, base_url, project_id: int):
    """Диагностика реальных проблем с задачами"""
    tasks = get_all_tasks(session, base_url, project_id)
    
    for task in tasks:
        task_id = task['id']
        task_name = task['name']
        
        print(f"\n🔍 Diagnosing: {task_name} (ID: {task_id})")
        print("-" * 50)
        
        # 1. Проверка превью (самый показательный тест)
        preview_response = session.get(f"{base_url}/api/tasks/{task_id}/data?type=preview")
        print(f"Preview: {preview_response.status_code}")
        
        # 2. Проверка метаданных
        meta_response = session.get(f"{base_url}/api/tasks/{task_id}/data/meta")
        if meta_response.status_code == 200:
            meta = meta_response.json()
            print(f"Frames: {len(meta.get('frames', []))}")
        else:
            print(f"Meta: {meta_response.status_code}")
        
        # 3. Проверка конкретного фрейма
        frame_response = session.get(f"{base_url}/api/tasks/{task_id}/data?type=frame&number=0")
        print(f"Frame 0: {frame_response.status_code}")


def force_refresh_task_data(session, base_url, task_id):
    """Принудительно обновить данные задачи (экспериментально)"""
    
    # Вариант 1: Обновление через data endpoint
    data_response = session.put(
        f"{base_url}/api/tasks/{task_id}/data",
        json={"image_quality": 100}  # Любые параметры чтобы триггернуть обновление
    )
    print(f"Data refresh: {data_response.status_code}")
    
    # Вариант 2: Перезапуск задачи
    restart_response = session.post(f"{base_url}/api/tasks/{task_id}/data?action=restart")
    print(f"Restart: {restart_response.status_code}")


def verify_share_paths(session, base_url, share_path, task_names):
    """Проверить что все пути в Share корректны"""
    print("🔎 Verifying share paths...")
    
    for task_name in task_names:
        full_path = f"{share_path}/{task_name}/obj_train_data"
        
        # Проверяем существование пути
        share_response = session.get(f"{base_url}/api/server/share?directory={full_path}")
        
        if share_response.status_code == 200:
            files = share_response.json()
            images = [f for f in files if f.get('name', '').lower().endswith(('.jpg', '.png', '.jpeg'))]
            print(f"✅ {task_name}: {len(images)} images")
        else:
            print(f"❌ {task_name}: Path not accessible")

base_url = "http://212.20.47.88:7555"
username = "Boroda-v-goroshek"
password = "RAlf2005"
session = create_session(base_url, username, password)
tasks = get_all_tasks(session, base_url, 35)
task_names = [task['name'] for task in tasks]
verify_share_paths(session, base_url, "shestakov/data_for_cvat", task_names)

