import yaml
import time

import requests


def get_cvat_data(path_to_yml: str) -> tuple[str, str, str]:
    if path_to_yml:
        with open(path_to_yml, "r", encoding="utf-8") as file:
            args = yaml.safe_load(file)
    else:
        raise ValueError("path_to_yml is empty or invalid")
        
    server_url = args["server_url"]
    username = args["username"]
    password = args["password"]

    return server_url, username, password


def upload_from_share_folders(directory_names: list[str], credentials, project_id, start_share_path):
    base_url = credentials["base_url"]
    username = credentials["username"]
    password = credentials["password"]

    
    session = requests.Session()
    
    print("Начинаем загрузку данных из CVAT share...")
    print("=" * 60)
    
    print("1. Аутентификация...")
    try:
        login_response = session.post(
            f"{base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=30
        )
        
        if login_response.status_code != 200:
            print(f"❌ Ошибка логина: {login_response.text}")
            return []
        
        auth_data = login_response.json()
        session.headers.update({"Authorization": f"Token {auth_data['key']}"})
        print("Успешно...✅")
        
    except Exception as e:
        print(f"❌ Ошибка при логине: {e}")
        return []
    
    results = {}
    
    for dir_name in directory_names:
        print(f"\nОбрабатываем директорию: {dir_name}")
        print("-" * 40)
        
        share_path = f"{start_share_path}/{dir_name}/obj_train_data"
        
        try:
            task_payload = {
                "name": dir_name,
                "project_id": project_id
            }
            
            create_response = session.post(
                f"{base_url}/api/tasks", 
                json=task_payload,
                timeout=30
            )
            
            if create_response.status_code not in [200, 201]:
                print(f"❌ Ошибка создания задачи: {create_response.text}")
                results[dir_name] = f"ERROR: failed to create task - {create_response.status_code}"
                continue
            
            task_data = create_response.json()
            task_id = task_data['id']
            print(f"Задача создана: {dir_name} (ID: {task_id})...✅")
            
            share_data = {
                "server_files": [f"{share_path}/"],
                "image_quality": 100,
                "use_zip_chunks": False,
                "sorting_method": "natural"
            }
            
            print(f"Загружаем данные из: {share_path}")
            upload_response = session.post(
                f"{base_url}/api/tasks/{task_id}/data",
                json=share_data,
                timeout=30
            )
            
            print(f"   Статус загрузки: {upload_response.status_code}")
            
            if upload_response.status_code in [200, 202]:
                print("Запрос на загрузку принят...✅")
                
                task_status = wait_for_upload_completion(session, base_url, task_id, dir_name)
                
                if task_status == "Finished":
                    results[dir_name] = f"SUCCESS: task {task_id}"
                    print(f"{dir_name} - успешно...✅")
                else:
                    results[dir_name] = f"ERROR: upload failed - {task_status}"
                    try:
                        session.delete(f"{base_url}/api/tasks/{task_id}")
                        print(f"Задача {task_id} удалена из-за ошибки")
                    except:
                        pass
            else:
                print(f"❌ Ошибка загрузки: {upload_response.text}")
                results[dir_name] = f"ERROR: upload request failed - {upload_response.status_code}"
                try:
                    session.delete(f"{base_url}/api/tasks/{task_id}")
                except:
                    pass
                
        except Exception as e:
            print(f"❌ Исключение при обработке {dir_name}: {e}")
            results[dir_name] = f"ERROR: exception - {str(e)}"
    
    print("\n" + "=" * 60)
    print("ИТОГИ ЗАГРУЗКИ:")
    print("=" * 60)
    
    success_count = 0
    for dir_name, status in results.items():
        if "SUCCESS" in status:
            print(f"✅ {dir_name}: {status}")
            success_count += 1
        else:
            print(f"❌ {dir_name}: {status}")
    
    print(f"\nУспешно загружено: {success_count}/{len(directory_names)}")
    return results


def wait_for_upload_completion(session, base_url, task_id, dir_name, max_wait=300):
    wait_interval = 5
    elapsed_time = 0
    
    while elapsed_time < max_wait:
        try:
            status_response = session.get(
                f"{base_url}/api/tasks/{task_id}/status",
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                state = status_data.get("state", "")
                message = status_data.get("message", "")
                
                if state == "Finished":
                    return "Finished"
                elif state == "Failed":
                    print(f"   ❌ Ошибка загрузки: {message}")
                    return f"Failed: {message}"
            
        except Exception as e:
            print(f"   ⚠ Ошибка проверки статуса: {e}")
        
        time.sleep(wait_interval)
        elapsed_time += wait_interval
    
    return "Timeout"


def check_share_access(session, base_url):
    print("\nПроверка доступа к share...")
    
    try:
        share_response = session.get(f"{base_url}/api/server/share")
        
        if share_response.status_code == 200:
            share_info = share_response.json()
            print("Доступ к share подтвержден...✅")
            return True
        else:
            print(f"⚠ Не удалось получить информацию о share: {share_response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠ Ошибка при проверке share: {e}")
        return True
