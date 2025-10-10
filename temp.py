import requests
import json
from typing import Dict, List

class CVATAnnotationUploader:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.authenticate(username, password)
        self.setup_csrf_headers()
    
    def authenticate(self, username: str, password: str):
        """Аутентификация в CVAT"""
        auth_url = f"{self.base_url}/api/auth/login"
        response = self.session.post(auth_url, json={
            "username": username,
            "password": password
        })
        if response.status_code != 200:
            raise Exception(f"Auth failed: {response.text}")
        print("✅ Успешная аутентификация")

    def setup_csrf_headers(self):
        """Настройка CSRF заголовков из кук"""
        csrf_token = self.get_csrf_from_cookies()
        if csrf_token:
            # Устанавливаем CSRF заголовки для ВСЕХ запросов
            self.session.headers.update({
                'X-CSRFToken': csrf_token,
                'Referer': self.base_url  # Часто требуется для CSRF
            })
            print(f"🔐 CSRF токен установлен: {csrf_token[:20]}...")
        else:
            print("❌ CSRF токен не найден в куках")

    def get_csrf_from_cookies(self):
        """Получение CSRF токена из кук"""
        for cookie in self.session.cookies:
            if 'csrftoken' in cookie.name:
                return cookie.value
        return None

    def upload_annotations_direct(self, job_id: int):
        """Загрузка аннотаций с правильным CSRF"""
        print(f"\n🎯 ЗАГРУЗКА АННОТАЦИЙ ДЛЯ JOB {job_id}")
        
        annotations_url = f"{self.base_url}/api/jobs/{job_id}/annotations"
        
        # 1. Получаем текущие аннотации
        print("\n1. 📥 Текущие аннотации:")
        response = self.session.get(annotations_url)
        if response.status_code == 200:
            current = response.json()
            print(f"   Версия: {current.get('version')}, Shapes: {len(current.get('shapes', []))}")
        
        # 2. Создаем тестовые аннотации
        test_annotation = self._create_test_annotation()
        print(f"\n2. 📤 Загружаем {len(test_annotation['shapes'])} shapes...")
        
        # 3. Загружаем аннотации
        response = self.session.put(annotations_url, json=test_annotation)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Успешно загружено!")
        else:
            print(f"   ❌ Ошибка: {response.text}")
            # Пробуем альтернативные методы
            self._try_alternative_upload_methods(job_id, test_annotation)
        
        # 4. Проверяем результат
        self._check_upload_result(job_id)

    def _try_alternative_upload_methods(self, job_id: int, annotation: Dict):
        """Альтернативные методы загрузки"""
        print("\n🔄 Пробуем альтернативные методы...")
        
        annotations_url = f"{self.base_url}/api/jobs/{job_id}/annotations"
        
        # Метод 1: PATCH
        print("   🔹 Метод PATCH:")
        response = self.session.patch(annotations_url, json=annotation)
        print(f"      Status: {response.status_code}")
        
        # Метод 2: POST
        print("   🔹 Метод POST:")
        response = self.session.post(annotations_url, json=annotation)
        print(f"      Status: {response.status_code}")
        
        # Метод 3: С дополнительными заголовками
        print("   🔹 С дополнительными заголовками:")
        headers = {
            'X-CSRFToken': self.get_csrf_from_cookies(),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        response = self.session.put(annotations_url, json=annotation, headers=headers)
        print(f"      Status: {response.status_code}")

    def upload_via_task_with_csrf(self, task_id: int):
        """Загрузка через задачу с CSRF"""
        print(f"\n📦 ЗАГРУЗКА ЧЕРЕЗ TASK {task_id}")
        
        task_annotations_url = f"{self.base_url}/api/tasks/{task_id}/annotations"
        
        # Метод 1: Прямые аннотации
        test_annotation = self._create_test_annotation()
        print("1. 📤 Прямые аннотации:")
        response = self.session.put(task_annotations_url, json=test_annotation)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            # Метод 2: CVAT формат
            print("2. 📤 CVAT 1.1 формат:")
            self._upload_cvat_format(task_id)

    def _upload_cvat_format(self, task_id: int):
        """Загрузка в формате CVAT 1.1"""
        import_url = f"{self.base_url}/api/tasks/{task_id}/annotations"
        
        cvat_xml = """<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <version>1.1</version>
  <meta>
    <task>
      <id>{task_id}</id>
      <name>Test Task</name>
      <size>421</size>
      <mode>annotation</mode>
      <labels>
        <label>
          <name>building_machine</name>
        </label>
        <label>
          <name>car</name>
        </label>
      </labels>
    </task>
  </meta>
  <image id="0" name="image0.jpg">
    <box label="building_machine" occluded="0" xtl="100" ytl="100" xbr="200" ybr="200">
    </box>
  </image>
  <image id="1" name="image1.jpg">
    <box label="car" occluded="0" xtl="150" ytl="150" xbr="250" ybr="250">
    </box>
  </image>
</annotations>""".format(task_id=task_id)
        
        files = {
            'annotation_file': ('annotations.xml', cvat_xml, 'application/xml')
        }
        
        data = {
            'format': 'CVAT 1.1'
        }
        
        response = self.session.put(import_url, files=files, data=data)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 202]:
            print("   ✅ Успешно!")
        else:
            print(f"   ❌ Ошибка: {response.text[:200]}")

    def debug_csrf_workflow(self):
        """Диагностика CSRF workflow"""
        print("\n🔧 ДИАГНОСТИКА CSRF:")
        
        # Текущие заголовки
        print("📋 Текущие заголовки сессии:")
        for key, value in self.session.headers.items():
            print(f"   {key}: {value}")
        
        # Проверяем CSRF эндпоинт
        csrf_url = f"{self.base_url}/api/auth/csrf"
        response = self.session.get(csrf_url)
        print(f"\n🔐 CSRF эндпоинт: {response.status_code}")
        if response.status_code == 200:
            print(f"   CSRF данные: {response.json()}")

    def _create_test_annotation(self) -> Dict:
        """Создание тестовой аннотации"""
        return {
            "version": 1,
            "tags": [],
            "shapes": [
                {
                    "type": "rectangle",
                    "occluded": False,
                    "frame": 0,
                    "label_id": 87,  # building_machine
                    "group": 0,
                    "source": "manual",
                    "attributes": [],
                    "points": [100.0, 100.0, 200.0, 200.0]
                },
                {
                    "type": "rectangle",
                    "occluded": False,
                    "frame": 1,
                    "label_id": 88,  # car
                    "group": 0,
                    "source": "manual",
                    "attributes": [],
                    "points": [150.0, 150.0, 250.0, 250.0]
                }
            ],
            "tracks": []
        }

    def _check_upload_result(self, job_id: int):
        """Проверка результата загрузки"""
        print("\n3. 🔍 Проверка результата:")
        annotations_url = f"{self.base_url}/api/jobs/{job_id}/annotations"
        response = self.session.get(annotations_url)
        
        if response.status_code == 200:
            updated = response.json()
            print(f"   Версия: {updated.get('version')}")
            print(f"   Shapes: {len(updated.get('shapes', []))}")
            print(f"   Tracks: {len(updated.get('tracks', []))}")
            print(f"   Tags: {len(updated.get('tags', []))}")
            
            if updated.get('shapes'):
                print("   🆕 Детали shapes:")
                for shape in updated.get('shapes', []):
                    print(f"     - Frame {shape.get('frame')}: {shape.get('type')} (label_id: {shape.get('label_id')})")

def main():
    CVAT_URL = "http://212.20.47.88:7555"
    USERNAME = "Boroda-v-goroshek"
    PASSWORD = "RAlf2005"  # замените на реальный
    
    try:
        uploader = CVATAnnotationUploader(CVAT_URL, USERNAME, PASSWORD)
        
        # Диагностика
        uploader.debug_csrf_workflow()
        
        # Основная загрузка
        job_id = 770
        task_id = 827
        
        uploader.upload_annotations_direct(job_id)
        
        # Если не сработало, пробуем через задачу
        # uploader.upload_via_task_with_csrf(task_id)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()