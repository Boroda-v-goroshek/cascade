import requests
from requests.auth import HTTPBasicAuth

def test_cvat_with_login():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    session = requests.Session()
    
    print("Тестируем логин и доступ к API...")
    print("=" * 50)
    
    # 1. Логинимся
    try:
        login_response = session.post(
            f"{base_url}/api/auth/login",
            data={
                "username": username,
                "password": password
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        print(f"1. Логин: HTTP {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("   ✓ Успешный логин!")
            print(f"   Ответ: {login_response.text[:100]}...")
        else:
            print(f"   ✗ Ошибка логина: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Ошибка при логине: {e}")
        return False
    
    # 2. Получаем информацию о пользователе
    try:
        user_response = session.get(f"{base_url}/api/users/self")
        print(f"2. Информация о пользователе: HTTP {user_response.status_code}")
        if user_response.status_code == 200:
            user_info = user_response.json()
            print(f"   ✓ Пользователь: {user_info.get('username', 'N/A')}")
        else:
            print(f"   ⚠ Не удалось получить информацию: {user_response.text}")
    except Exception as e:
        print(f"   ⚠ Ошибка: {e}")
    
    # 3. Получаем список проектов
    try:
        projects_response = session.get(f"{base_url}/api/projects")
        print(f"3. Список проектов: HTTP {projects_response.status_code}")
        if projects_response.status_code == 200:
            projects_data = projects_response.json()
            projects_count = projects_data.get('count', len(projects_data.get('results', [])))
            print(f"   ✓ Найдено проектов: {projects_count}")
            
            # Покажем первые 3 проекта
            for project in projects_data.get('results', [])[:3]:
                print(f"     - {project['name']} (ID: {project['id']})")
        else:
            print(f"   ✗ Ошибка: {projects_response.text}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
    
    # 4. Получаем список задач
    try:
        tasks_response = session.get(f"{base_url}/api/tasks")
        print(f"4. Список задач: HTTP {tasks_response.status_code}")
        if tasks_response.status_code == 200:
            tasks_data = tasks_response.json()
            tasks_count = tasks_data.get('count', len(tasks_data.get('results', [])))
            print(f"   ✓ Найдено задач: {tasks_count}")
        else:
            print(f"   ✗ Ошибка: {tasks_response.text}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
    
    # 5. Создаем тестовую задачу
    try:
        task_data = {
            "name": "test_task_api",
            "project_id": None
        }
        create_response = session.post(
            f"{base_url}/api/tasks",
            json=task_data
        )
        print(f"5. Создание задачи: HTTP {create_response.status_code}")
        if create_response.status_code in [200, 201]:
            task_info = create_response.json()
            print(f"   ✓ Задача создана (ID: {task_info['id']})")
            
            # Удаляем тестовую задачу
            delete_response = session.delete(f"{base_url}/api/tasks/{task_info['id']}")
            if delete_response.status_code in [200, 204]:
                print("   ✓ Тестовая задача удалена")
            else:
                print(f"   ⚠ Не удалось удалить задачу")
        else:
            print(f"   ⚠ Не удалось создать задачу: {create_response.text}")
    except Exception as e:
        print(f"   ⚠ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print("Тестирование завершено!")
    return True


def debug_cvat_http():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    print(f"Отладочная информация для {base_url}")
    print("=" * 50)
    
    # Проверим что возвращает endpoint /auth/whoami
    print("1. Проверка /auth/whoami...")
    try:
        response = requests.get(
            f"{base_url}/auth/whoami",
            auth=HTTPBasicAuth(username, password),
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Response Text: '{response.text}'")
        print(f"   Response Length: {len(response.text)}")
        
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Проверим другие endpoints без аутентификации
    print("\n2. Проверка endpoints без аутентификации...")
    endpoints = [
        "/auth/whoami",
        "/api/projects",
        "/api/tasks", 
        "/api/server/about",
        "/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   {endpoint}: ошибка {e}")
    
    # Проверим с неправильным паролем
    print("\n3. Проверка с неверными credentials...")
    try:
        response = requests.get(
            f"{base_url}/auth/whoami",
            auth=HTTPBasicAuth(username, "wrong_password"),
            timeout=10
        )
        print(f"   С неверным паролем: HTTP {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")


def test_cvat_with_session():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "your_password"
    
    print("Тестируем сессионную аутентификацию...")
    
    # Создаем сессию
    session = requests.Session()
    
    # 1. Сначала получаем CSRF токен со страницы логина
    print("1. Получаем CSRF токен...")
    try:
        response = session.get(f"{base_url}/auth/login")
        print(f"   Страница логина: HTTP {response.status_code}")
        
        # Ищем CSRF токен в HTML
        if 'csrf' in response.text:
            print("   ✓ CSRF токен найден в ответе")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # 2. Пробуем аутентификацию через форму логина
    print("\n2. Пробуем аутентификацию через форму...")
    try:
        login_data = {
            'username': username,
            'password': password,
            # Может потребоваться CSRF токен
        }
        
        response = session.post(
            f"{base_url}/auth/login",
            data=login_data,
            allow_redirects=False
        )
        print(f"   Логин: HTTP {response.status_code}")
        print(f"   Куки после логина: {dict(session.cookies)}")
        
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # 3. Проверяем доступ к API после логина
    print("\n3. Проверяем API с сессией...")
    try:
        response = session.get(f"{base_url}/api/projects")
        print(f"   /api/projects: HTTP {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"   ✓ Успех! Проектов: {projects.get('count', 'N/A')}")
        else:
            print(f"   Ответ: {response.text[:100]}...")
            
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    return session

# Альтернативный вариант - используем API ключ если доступен
def test_with_api_key():
    base_url = "http://212.20.47.88:7555"
    
    print("\n" + "="*50)
    print("Проверка с API ключом...")
    
    # Попробуйте найти API ключ в настройках CVAT
    api_key = "your_api_key_here"  # Нужно получить из UI CVAT
    
    headers = {
        'Authorization': f'Token {api_key}'
    }
    
    try:
        response = requests.get(
            f"{base_url}/api/projects",
            headers=headers,
            timeout=10
        )
        print(f"   /api/projects с API ключом: HTTP {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"   ✓ Успех с API ключом! Проектов: {projects.get('count', 'N/A')}")
        else:
            print(f"   Ответ: {response.text[:100]}...")
            
    except Exception as e:
        print(f"   Ошибка: {e}")

# if __name__ == "__main__":
#     session = test_cvat_with_session()
#     test_with_api_key()

# if __name__ == "__main__":
#     debug_cvat_http()

# if __name__ == "__main__":
#     test_cvat_with_login()

def find_auth_endpoint():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "password"
    
    print("Поиск правильного endpoint для аутентификации...")
    print("=" * 50)
    
    # Попробуем различные варианты auth endpoints
    auth_endpoints = [
        "/api/auth/login",
        "/auth/login", 
        "/api/auth/token",
        "/auth/token",
        "/api/auth",
        "/api/login",
        "/login",
        "/api/auth/basic/login",
        "/api/auth/credentials"
    ]
    
    for endpoint in auth_endpoints:
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                auth=HTTPBasicAuth(username, password),
                timeout=10
            )
            print(f"{endpoint}:")
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code == 200:
                # Проверим, это JSON или HTML
                if 'application/json' in response.headers.get('content-type', ''):
                    print(f"  ✓ Возможно это правильный endpoint!")
                    print(f"  Response: {response.text[:100]}...")
                else:
                    print(f"  ⚠ Возвращает HTML (не JSON)")
            print()
            
        except Exception as e:
            print(f"{endpoint}: ошибка - {e}\n")
    
    # Также попробуем POST запрос для логина
    print("Проверка POST запросов для логина...")
    post_endpoints = [
        "/api/auth/login",
        "/auth/login",
        "/api/login"
    ]
    
    for endpoint in post_endpoints:
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json={"username": username, "password": password},
                timeout=10
            )
            print(f"POST {endpoint}:")
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
            if response.status_code == 200:
                print(f"  Response: {response.text[:100]}...")
            print()
            
        except Exception as e:
            print(f"POST {endpoint}: ошибка - {e}\n")

# if __name__ == "__main__":
#     find_auth_endpoint()

import json

def test_cvat_login_formats():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    session = requests.Session()
    
    print("Тестируем разные форматы данных для логина...")
    print("=" * 50)
    
    # Варианты данных для логина
    login_attempts = [
        {
            "name": "JSON с username/password",
            "data": json.dumps({"username": username, "password": password}),
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "JSON с email вместо username",
            "data": json.dumps({"email": username, "password": password}),
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "JSON с ключами в верхнем регистре",
            "data": json.dumps({"Username": username, "Password": password}),
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "Form data с другим Content-Type",
            "data": {"username": username, "password": password},
            "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
        },
        {
            "name": "Form data как multipart",
            "data": {"username": username, "password": password},
            "headers": {"Content-Type": "multipart/form-data"}
        },
        {
            "name": "CVAT-specific JSON",
            "data": json.dumps({"username": username, "password": password}),
            "headers": {"Content-Type": "application/vnd.cvat+json"}
        }
    ]
    
    for attempt in login_attempts:
        print(f"\nПопытка: {attempt['name']}")
        try:
            login_response = session.post(
                f"{base_url}/api/auth/login",
                data=attempt["data"],
                headers=attempt["headers"]
            )
            print(f"  Status: {login_response.status_code}")
            print(f"  Response: {login_response.text[:200]}...")
            
            if login_response.status_code == 200:
                print("  ✓ УСПЕШНЫЙ ЛОГИН!")
                # Проверим доступ к API
                projects_response = session.get(f"{base_url}/api/projects")
                print(f"  Проверка API: Projects - HTTP {projects_response.status_code}")
                break
                
        except Exception as e:
            print(f"  Ошибка: {e}")

# if __name__ == "__main__":
#     test_cvat_login_formats()

import requests
import json

def test_cvat_full_access():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    session = requests.Session()
    
    print("Полное тестирование доступа к CVAT API")
    print("=" * 50)
    
    # 1. Логинимся
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"✗ Ошибка логина: {login_response.text}")
        return False
    
    auth_data = login_response.json()
    auth_key = auth_data.get("key")
    print(f"✓ Успешный логин")
    print(f"  Auth key: {auth_key[:20]}...")
    
    # Добавляем авторизацию в заголовки
    session.headers.update({
        "Authorization": f"Token {auth_key}"
    })
    
    # 2. Получаем информацию о пользователе
    user_response = session.get(f"{base_url}/api/users/self")
    if user_response.status_code == 200:
        user_info = user_response.json()
        print(f"✓ Пользователь: {user_info.get('username')}")
        print(f"  ID: {user_info.get('id')}, Email: {user_info.get('email')}")
    else:
        print(f"⚠ Не удалось получить информацию о пользователе")
    
    # 3. Получаем проекты
    projects_response = session.get(f"{base_url}/api/projects")
    if projects_response.status_code == 200:
        projects_data = projects_response.json()
        projects = projects_data.get('results', [])
        print(f"✓ Найдено проектов: {len(projects)}")
        
        for project in projects[:5]:  # Покажем первые 5
            print(f"  - {project['name']} (ID: {project['id']})")
    else:
        print(f"✗ Ошибка получения проектов: {projects_response.text}")
    
    # 4. Получаем задачи
    tasks_response = session.get(f"{base_url}/api/tasks")
    if tasks_response.status_code == 200:
        tasks_data = tasks_response.json()
        tasks = tasks_data.get('results', [])
        print(f"✓ Найдено задач: {len(tasks)}")
        
        for task in tasks[:3]:  # Покажем первые 3
            print(f"  - {task['name']} (ID: {task['id']}, Status: {task['status']})")
    else:
        print(f"✗ Ошибка получения задач: {tasks_response.text}")
    
    # 5. Создаем и удаляем тестовую задачу
    test_task_data = {
        "name": "test_api_task",
        "project_id": "fsra"
    }
    
    create_response = session.post(
        f"{base_url}/api/tasks",
        json=test_task_data
    )
    
    if create_response.status_code in [200, 201]:
        task_info = create_response.json()
        task_id = task_info['id']
        print(f"✓ Тестовая задача создана (ID: {task_id})")
        
        # Удаляем тестовую задачу
        delete_response = session.delete(f"{base_url}/api/tasks/{task_id}")
        if delete_response.status_code in [200, 204]:
            print(f"✓ Тестовая задача удалена")
        else:
            print(f"⚠ Не удалось удалить задачу: {delete_response.text}")
    else:
        print(f"⚠ Не удалось создать тестовую задачу: {create_response.text}")
    
    print("\n" + "=" * 50)
    print("✅ CVAT API полностью доступен!")
    return True

# if __name__ == "__main__":
#     test_cvat_full_access()


def explore_task_creation():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    session = requests.Session()
    
    # Логинимся
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password}
    )
    auth_data = login_response.json()
    session.headers.update({"Authorization": f"Token {auth_data['key']}"})
    
    print("Исследуем создание задач...")
    print("=" * 50)
    
    # 1. Посмотрим на существующие задачи чтобы понять структуру
    tasks_response = session.get(f"{base_url}/api/tasks")
    if tasks_response.status_code == 200:
        tasks = tasks_response.json().get('results', [])
        if tasks:
            print("Существующие задачи (структура):")
            task = tasks[0]
            print(f"  Поля: {list(task.keys())}")
            print(f"  Пример: name='{task['name']}', project_id={task.get('project_id')}")
            print(f"  Status: {task.get('status')}")
            print(f"  Mode: {task.get('mode')}")
    
    # 2. Проверим OPTIONS для /api/tasks
    options_response = session.options(f"{base_url}/api/tasks")
    print(f"\nOPTIONS /api/tasks: {options_response.status_code}")
    if options_response.status_code == 200:
        print(f"  Headers: {dict(options_response.headers)}")
    
    # 3. Попробуем разные варианты данных для создания задачи
    test_payloads = [
        {"name": "test_task_simple", "labels": [{"name": "test_label"}]},
        {"name": "test_task_with_project", "project_id": 35},  # ID проекта fsra
        {"name": "test_task_full", "project_id": 35, "labels": [{"name": "object"}]},
        {"name": "test_task_mode", "project_id": 35, "mode": "annotation", "labels": [{"name": "test"}]},
    ]
    
    for i, payload in enumerate(test_payloads):
        print(f"\nПопытка {i+1}: {payload}")
        try:
            response = session.post(f"{base_url}/api/tasks", json=payload)
            print(f"  Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                task_data = response.json()
                print(f"  ✅ УСПЕХ! Создана задача ID: {task_data['id']}")
                
                # Удаляем тестовую задачу
                delete_response = session.delete(f"{base_url}/api/tasks/{task_data['id']}")
                print(f"  Удаление: {delete_response.status_code}")
                break
            else:
                print(f"  ❌ Ошибка: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  ❌ Исключение: {e}")

def test_with_existing_project():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    session = requests.Session()
    
    # Логинимся
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password}
    )
    auth_data = login_response.json()
    session.headers.update({"Authorization": f"Token {auth_data['key']}"})
    
    print("\n" + "=" * 50)
    print("Тест с существующим проектом 'fsra' (ID: 35)")
    print("=" * 50)
    
    # Получим информацию о проекте fsra
    project_response = session.get(f"{base_url}/api/projects/35")
    if project_response.status_code == 200:
        project_data = project_response.json()
        print(f"Проект: {project_data['name']}")
        print(f"Лейблы: {[label['name'] for label in project_data.get('labels', [])]}")
        
        # Создадим задачу с лейблами из проекта
        task_payload = {
            "name": "api_test_task",
            "project_id": 35,
        }
        
        response = session.post(f"{base_url}/api/tasks", json=task_payload)
        print(f"Создание задачи: {response.status_code}")
        
        if response.status_code in [200, 201]:
            task_data = response.json()
            print(f"✅ Задача создана! ID: {task_data['id']}")
            
            # Проверим что задача действительно создалась
            task_check = session.get(f"{base_url}/api/tasks/{task_data['id']}")
            if task_check.status_code == 200:
                print(f"✅ Задача подтверждена: {task_check.json()['name']}")
            
            # Удаляем
            delete_response = session.delete(f"{base_url}/api/tasks/{task_data['id']}")
            print(f"Удаление: {delete_response.status_code}")
        else:
            print(f"❌ Ошибка: {response.text}")

# if __name__ == "__main__":
#     explore_task_creation()
#     test_with_existing_project()


def create_task_with_labels():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    session = requests.Session()
    
    # Логинимся
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password}
    )
    auth_data = login_response.json()
    session.headers.update({"Authorization": f"Token {auth_data['key']}"})
    
    print("Создание задачи с лейблами...")
    print("=" * 50)
    
    # Создаем задачу с лейблами
    task_payload = {
        "name": "test_task_with_labels",
        "labels": [
            {"name": "object"},
            {"name": "person"},
            {"name": "car"}
        ]
    }
    
    response = session.post(f"{base_url}/api/tasks", json=task_payload)
    print(f"Создание задачи: {response.status_code}")
    
    if response.status_code in [200, 201]:
        task_data = response.json()
        print(f"✅ Задача создана! ID: {task_data['id']}")
        print(f"   Name: {task_data['name']}")
        print(f"   Status: {task_data['status']}")
        
        # Удаляем тестовую задачу
        delete_response = session.delete(f"{base_url}/api/tasks/{task_data['id']}")
        print(f"✅ Удаление задачи: {delete_response.status_code}")
        
        return True
    else:
        print(f"❌ Ошибка: {response.text}")
        return False

def create_task_in_project():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    session = requests.Session()
    
    # Логинимся
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password}
    )
    auth_data = login_response.json()
    session.headers.update({"Authorization": f"Token {auth_data['key']}"})
    
    print("\nСоздание задачи в проекте...")
    print("=" * 50)
    
    # Создаем задачу в проекте (лейблы берутся из проекта)
    task_payload = {
        "name": "test_task_in_project",
        "project_id": 35  # ID проекта fsra
    }
    
    response = session.post(f"{base_url}/api/tasks", json=task_payload)
    print(f"Создание задачи в проекте: {response.status_code}")
    
    if response.status_code in [200, 201]:
        task_data = response.json()
        print(f"✅ Задача создана в проекте! ID: {task_data['id']}")
        
        return True
    else:
        print(f"❌ Ошибка: {response.text}")
        return False

# if __name__ == "__main__":
#     create_task_with_labels()
#     create_task_in_project()


import requests
import json
import time
from pathlib import Path

def upload_archive_to_cvat():
    base_url = "http://212.20.47.88:7555"
    username = "Boroda-v-goroshek"
    password = "RAlf2005"
    
    # Параметры задачи
    project_id = 35  # ID проекта fsra
    archive_path = Path("data/test_images.zip")
    task_name = "archive_upload_task"
    
    session = requests.Session()
    
    print("Создание задачи и загрузка архива...")
    print("=" * 50)
    
    # 1. Логинимся
    print("1. Аутентификация...")
    try:
        login_response = session.post(
            f"{base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=30
        )
        
        if login_response.status_code != 200:
            print(f"❌ Ошибка логина:")
            print(f"   Status: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            print(f"   Headers: {dict(login_response.headers)}")
            return None
        
        auth_data = login_response.json()
        session.headers.update({"Authorization": f"Token {auth_data['key']}"})
        print("✅ Успешный логин")
        
    except Exception as e:
        print(f"❌ Исключение при логине: {e}")
        return None
    
    # 2. Создаем задачу в проекте
    print("2. Создание задачи...")
    try:
        task_payload = {
            "name": task_name,
            "project_id": project_id
        }
        
        create_response = session.post(
            f"{base_url}/api/tasks", 
            json=task_payload,
            timeout=30
        )
        
        print(f"   Status: {create_response.status_code}")
        print(f"   Headers: {dict(create_response.headers)}")
        
        if create_response.status_code not in [200, 201]:
            print(f"❌ Ошибка создания задачи:")
            print(f"   Response: {create_response.text}")
            return None
        
        task_data = create_response.json()
        task_id = task_data['id']
        print(f"✅ Задача создана: {task_name} (ID: {task_id})")
        
    except Exception as e:
        print(f"❌ Исключение при создании задачи: {e}")
        return None
    
    # 3. Загружаем данные из архива
    print("3. Загрузка архива...")
    
    # Проверяем существование архива
    if not archive_path.exists():
        print(f"❌ Архив не найден: {archive_path}")
        print(f"   Абсолютный путь: {archive_path.absolute()}")
        # Удаляем задачу если архив не найден
        try:
            session.delete(f"{base_url}/api/tasks/{task_id}")
        except:
            pass
        return None
    
    print(f"   Архив найден: {archive_path}")
    print(f"   Размер: {archive_path.stat().st_size} bytes")
    
    try:
        with open(archive_path, 'rb') as f:
            files = {
                'client_files[0]': (archive_path.name, f, 'application/zip')
            }
            data = {
                'image_quality': 70
            }
            
            print(f"   Отправка запроса на загрузку...")
            upload_response = session.post(
                f"{base_url}/api/tasks/{task_id}/data",
                files=files,
                data=data,
                timeout=60  # Увеличиваем таймаут для загрузки
            )
            
            print(f"   Status: {upload_response.status_code}")
            print(f"   Headers: {dict(upload_response.headers)}")
            print(f"   Response: {upload_response.text}")
            
            if upload_response.status_code not in [200, 202]:
                print(f"❌ Ошибка загрузки данных:")
                print(f"   Status: {upload_response.status_code}")
                print(f"   Response: {upload_response.text}")
                print(f"   Headers: {dict(upload_response.headers)}")
                
                # Удаляем задачу при ошибке загрузки
                try:
                    session.delete(f"{base_url}/api/tasks/{task_id}")
                except:
                    pass
                return None
            
            print("✅ Запрос на загрузку принят сервером")
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут при загрузке архива")
        try:
            session.delete(f"{base_url}/api/tasks/{task_id}")
        except:
            pass
        return None
    except Exception as e:
        print(f"❌ Исключение при загрузке архива: {e}")
        try:
            session.delete(f"{base_url}/api/tasks/{task_id}")
        except:
            pass
        return None
    
    # 4. Ждем завершения загрузки
    print("4. Ожидание завершения загрузки...")
    max_wait_time = 300  # 5 минут максимум
    wait_interval = 5    # проверяем каждые 5 секунд
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        try:
            status_response = session.get(
                f"{base_url}/api/tasks/{task_id}/status",
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                state = status_data.get("state", "")
                message = status_data.get("message", "")
                
                print(f"   Статус: {state} ({elapsed_time} сек.)")
                if message:
                    print(f"   Сообщение: {message}")
                
                if state == "Finished":
                    print("✅ Загрузка завершена!")
                    break
                elif state == "Failed":
                    print("❌ Ошибка загрузки данных")
                    print(f"   Сообщение об ошибке: {message}")
                    try:
                        session.delete(f"{base_url}/api/tasks/{task_id}")
                    except:
                        pass
                    return None
            else:
                print(f"   Ошибка получения статуса: {status_response.status_code}")
                
        except Exception as e:
            print(f"   Исключение при проверке статуса: {e}")
        
        time.sleep(wait_interval)
        elapsed_time += wait_interval
    
    if elapsed_time >= max_wait_time:
        print("⚠ Превышено время ожидания загрузки")
    
    # 5. Получаем информацию о созданной задаче
    try:
        task_info_response = session.get(f"{base_url}/api/tasks/{task_id}")
        if task_info_response.status_code == 200:
            task_info = task_info_response.json()
            print(f"\n📊 Информация о задаче:")
            print(f"   Название: {task_info['name']}")
            print(f"   Статус: {task_info['status']}")
            print(f"   Размер: {task_info.get('size', 'N/A')}")
            print(f"   Количество сегментов: {len(task_info.get('segments', []))}")
        else:
            print(f"⚠ Не удалось получить информацию о задаче: {task_info_response.status_code}")
    except Exception as e:
        print(f"⚠ Исключение при получении информации о задаче: {e}")
    
    return task_id

def main():
    task_id = upload_archive_to_cvat()
    
    if task_id:
        print(f"\n🎉 Задача успешно создана и данные загружены!")
        print(f"   ID задачи: {task_id}")
        print(f"   Ссылка: http://212.20.47.88:7555/tasks/{task_id}")
    else:
        print(f"\n💥 Не удалось создать задачу")

if __name__ == "__main__":
    main()


import zipfile
import os
from pathlib import Path

def check_archive_structure(archive_path):
    """Проверяет структуру архива и содержимое"""
    print(f"🔍 Анализ архива: {archive_path}")
    print("=" * 50)
    
    if not archive_path.exists():
        print("❌ Архив не существует")
        return False
    
    # Проверяем что это ZIP архив
    if not zipfile.is_zipfile(archive_path):
        print("❌ Это не ZIP архив")
        return False
    
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            # Получаем список файлов
            file_list = zip_ref.namelist()
            
            print(f"📁 Файлов в архиве: {len(file_list)}")
            
            if len(file_list) == 0:
                print("❌ Архив пустой")
                return False
            
            # Анализируем файлы
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
            image_files = []
            other_files = []
            
            for file in file_list:
                file_path = Path(file)
                if file_path.suffix.lower() in image_extensions:
                    image_files.append(file)
                else:
                    other_files.append(file)
            
            print(f"🖼️  Изображений найдено: {len(image_files)}")
            print(f"📄 Других файлов: {len(other_files)}")
            
            # Показываем структуру
            if image_files:
                print("\n📋 Найденные изображения:")
                for img in image_files[:10]:  # Показываем первые 10
                    print(f"   - {img}")
                if len(image_files) > 10:
                    print(f"   ... и еще {len(image_files) - 10} изображений")
            
            if other_files:
                print("\n📋 Другие файлы:")
                for other in other_files[:10]:
                    print(f"   - {other}")
                if len(other_files) > 10:
                    print(f"   ... и еще {len(other_files) - 10} файлов")
            
            # Проверяем структуру папок
            has_folders = any('/' in file for file in file_list)
            print(f"\n📂 Структура папок: {'Есть' if has_folders else 'Нет'}")
            
            return len(image_files) > 0
            
    except Exception as e:
        print(f"❌ Ошибка при анализе архива: {e}")
        return False

def test_small_archive():
    """Создает тестовый архив с изображениями для проверки"""
    print("\n🧪 Создание тестового архива...")
    
    # Создаем временную папку с тестовыми изображениями
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # Создаем несколько простых PNG изображений программно
    try:
        from PIL import Image
        import io
        
        # Создаем простое изображение
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_dir / "test1.png")
        
        img = Image.new('RGB', (100, 100), color='blue') 
        img.save(test_dir / "test2.png")
        
        img = Image.new('RGB', (100, 100), color='green')
        img.save(test_dir / "test3.png")
        
        print("✅ Созданы тестовые изображения")
        
    except ImportError:
        print("⚠ PIL не установлен, пропускаем создание тестовых изображений")
        return None
    
    # Создаем архив
    test_archive = Path("test_images.zip")
    with zipfile.ZipFile(test_archive, 'w') as zipf:
        for img_file in test_dir.glob("*.png"):
            zipf.write(img_file, img_file.name)
    
    print(f"✅ Создан тестовый архив: {test_archive}")
    return test_archive

# def main():
#     archive_path = Path("data/abbandoned4_2.zip")
    
#     # Проверяем текущий архив
#     is_valid = check_archive_structure(archive_path)
    
#     if not is_valid:
#         print("\n❌ Проблема с архивом!")
#         print("\nВозможные причины:")
#         print("1. Архив пустой")
#         print("2. В архиве нет изображений (только другие файлы)")
#         print("3. Формат изображений не поддерживается")
#         print("4. Изображения находятся во вложенных папках")
        
#         # Создаем тестовый архив для проверки
#         test_archive = test_small_archive()
#         if test_archive:
#             print(f"\n🎯 Попробуйте загрузить тестовый архив: {test_archive}")
#             print("   Если он заработает - проблема в вашем архиве")
    
#     else:
#         print("\n✅ Архив выглядит корректно")
#         print("Попробуйте:")
#         print("1. Убедитесь что изображения не повреждены")
#         print("2. Попробуйте другой формат (PNG вместо JPG или наоборот)")
#         print("3. Уменьшите размер изображений")

# if __name__ == "__main__":
#     main()

