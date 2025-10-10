
from pathlib import Path

def find_deepest_directory(path):
    """
    Находит самую глубокую директорию в дереве, не содержащую поддиректорий.
    
    Args:
        path (str): Путь к начальной директории
        
    Returns:
        str: Исходный путь, если нет поддиректорий, 
             или путь к самой глубокой директории в дереве
    """
    path = Path(path)
    
    # Проверяем, что путь существует и является директорией
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Путь '{path}' не существует или не является директорией")
    
    def has_subdirectories(dir_path):
        """Проверяет, есть ли в директории поддиректории."""
        try:
            for item in dir_path.iterdir():
                if item.is_dir():
                    return True
            return False
        except PermissionError:
            # Если нет прав доступа к директории, считаем что поддиректорий нет
            return False
    
    # Если в текущей директории нет поддиректорий, возвращаем её
    if not has_subdirectories(path):
        return str(path)
    
    # Ищем самую глубокую директорию
    current_path = path
    while True:
        # Получаем все поддиректории
        subdirs = []
        try:
            for item in current_path.iterdir():
                if item.is_dir():
                    subdirs.append(item)
        except PermissionError:
            # Если нет прав доступа, останавливаемся на текущей директории
            break
        
        # Если нет поддиректорий, возвращаем текущий путь
        if not subdirs:
            break
        
        # Выбираем одну директорию для дальнейшего обхода
        # Можно выбрать первую, последнюю или по какому-то критерию
        # В данном случае выбираем первую в алфавитном порядке
        if subdirs:
            # Сортируем для детерминированного поведения
            subdirs.sort()
            current_path = subdirs[0]
        else:
            break
    
    return str(current_path)


# Альтернативная версия, которая ищет самую глубокую директорию в целом дереве
def find_deepest_directory_alt(path):
    """
    Альтернативная версия: находит самую глубокую директорию в дереве.
    
    Args:
        path (str): Путь к начальной директории
        
    Returns:
        str: Путь к самой глубокой директории в дереве
    """
    path = Path(path)
    
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Путь '{path}' не существует или не является директорией")
    
    def get_deepest_dir(current_path, max_depth_path, max_depth):
        """Рекурсивно находит самую глубокую директорию."""
        try:
            subdirs = [item for item in current_path.iterdir() if item.is_dir()]
        except PermissionError:
            return max_depth_path, max_depth
        
        # Если нет поддиректорий, проверяем глубину
        if not subdirs:
            current_depth = len(current_path.parts)
            if current_depth > max_depth:
                return current_path, current_depth
            else:
                return max_depth_path, max_depth
        
        # Рекурсивно обходим все поддиректории
        for subdir in subdirs:
            max_depth_path, max_depth = get_deepest_dir(subdir, max_depth_path, max_depth)
        
        return max_depth_path, max_depth
    
    # Начинаем поиск с исходной директории
    deepest_path, _ = get_deepest_dir(path, path, len(path.parts))
    return str(deepest_path)


# Пример использования
if __name__ == "__main__":
    test_path = "exports/35/282_Дорожная_ул_вл_3_корп_19_вл_3_корп_19_стр_1_3-7"
    
    # Создадим тестовую структуру для демонстрации
    test_structure = [
        "exports/35/282_Дорожная_ул_вл_3_корп_19_вл_3_корп_19_стр_1_3-7/obj_train_data/shestakov/data_for_cvat/282_Дорожная_ул_вл_3_корп_19_вл_3_корп_19_стр_1_3-7/obj_train_data"
    ]
    
    result = find_deepest_directory(test_path)
    print(f"Результат: {result}")
    
    # Альтернативная версия
    result_alt = find_deepest_directory_alt(test_path)
    print(f"Альтернативный результат: {result_alt}")