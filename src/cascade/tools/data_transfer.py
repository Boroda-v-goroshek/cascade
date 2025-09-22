import subprocess
import getpass
import json
from pathlib import Path
from typing import Dict

class DataTransfer:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.servers_config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load servers configurations."""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Конфигурационный файл {self.config_file} не найден")
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {e}")
    
    def transfer_data(self, local_path: str, remote_path: str, server_name: str, mode: str):
        """Copy data for scp.
        
        Parameters
        ----------
        local_path: str
            Path to local data
        remote_path: str 
            Path to remote data dir
        server_name: str
            Server name from configs/servers.json
        mode: str
            Copy or download
        """
        try:
            if not Path(local_path).exists():
                raise FileNotFoundError(f"Локальный путь не существует: {local_path}")
            
            server_info = self.servers_config.get(server_name)
            if not server_info:
                raise ValueError(f"Сервер '{server_name}' не найден в конфигурации")
            
            server_ip = server_info.get('ip')
            server_port = server_info.get('port', 22)
            
            if not server_ip:
                raise ValueError(f"Для сервера '{server_name}' не указан IP-адрес")
            
            username = getpass.getuser()


            if mode == 'copy':
                scp_command = [
                    'scp',
                    '-r',
                    '-P', str(server_port),
                    local_path,
                    f"{username}@{server_ip}:{remote_path}"
                ]
            elif mode == 'download':
                scp_command = [
                    'scp',
                    '-r',
                    '-P', str(server_port),
                    f"{username}@{server_ip}:{remote_path}",
                    local_path
                ]
            
            print(f"Копирование {local_path} -> {server_name}:{remote_path}")
            result = subprocess.run(
                scp_command, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
            print("✓ Копирование завершено успешно")
            if result.stdout:
                print(f"Output: {result.stdout}")
            
        except subprocess.TimeoutExpired:
            print("✗ Таймаут при выполнении SCP команды")
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка SCP: {e.stderr if e.stderr else str(e)}")
        except Exception as e:
            print(f"✗ Произошла ошибка: {e}")
