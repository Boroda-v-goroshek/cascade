import time
from typing import Optional

import requests
import yaml
import pandas as pd

from src.cascade.tables.table import TableEditor


class CvatCore:
    def __init__(self, credentials_path: str):
        """
        Base class for CVAT operations.

        Parameters
        ----------
        credentials_path : str
            Path to YAML file with CVAT credentials
        """
        self.read_cvat_data(credentials_path)

    def read_cvat_data(self, path_to_yml: str) -> tuple[str, str, str]:
        """
        Download credentials data from YAML file.

        Parameters
        ----------
        path_to_yml : str
            Path to credentials file

        Returns
        -------
        tuple[str, str, str]
            Server URL, username and password
        """
        if not path_to_yml:
            raise ValueError("path_to_yml is empty or invalid")

        with open(path_to_yml, "r", encoding="utf-8") as file:
            args = yaml.safe_load(file)

        self.base_url = args["base_url"]
        self.username = args["username"]
        self.password = args["password"]

        return self.base_url, self.username, self.password

    def _create_session(self) -> requests.Session:
        """
        Create authenticated session with CVAT.

        Returns
        -------
        requests.Session
            Authenticated session
        """
        session = requests.Session()
        
        login_response = session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": self.username, "password": self.password},
            timeout=30,
        )

        if login_response.status_code != 200:
            raise Exception(f"Login failed: {login_response.text}")

        auth_data = login_response.json()
        session.headers.update({"Authorization": f"Token {auth_data['key']}"})
        
        return session

    def _get_share_directories(self, share_path: str) -> list[str]:
        """
        Get list of directory names from CVAT share path.

        Parameters
        ----------
        share_path : str
            Path to data on CVAT share

        Returns
        -------
        list[str]
            List of directory names
        """
        session = self._create_session()
        
        try:
            share_list_response = session.get(
                f"{self.base_url}/api/server/share?directory={share_path}",
                timeout=30
            )

            if share_list_response.status_code == 200:
                share_data = share_list_response.json()
                directories = []
                
                for item in share_data:
                    if isinstance(item, dict) and item.get("type") == "DIR":
                        directories.append(item.get("name", ""))
                
                print(f"Found {len(directories)} directories in {share_path}")
                return directories
            else:
                print("❌ Cannot get directory list from share!")
                return []
                
        except Exception as e:
            print(f"❌ Error getting directory list: {e}")
            return []
        
        finally:
            session.close()

    def wait_for_load_completion(
        self, 
        session: requests.Session, 
        task_id: int, 
        max_wait: int = 300,
        wait_interval: int = 5
    ) -> str:
        """
        Wait for download/upload data to task to complete.

        Parameters
        ----------
        session : requests.Session
            Active session
        task_id : int
            ID for target task
        max_wait : int, optional
            Max time in seconds for waiting download, by default 300
        wait_interval : int, optional
            Interval between status checks in seconds, by default 5

        Returns
        -------
        str
            Status of loading process
        """
        elapsed_time = 0
        
        while elapsed_time < max_wait:
            try:
                status_response = session.get(
                    f"{self.base_url}/api/tasks/{task_id}/status", 
                    timeout=10
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    state = status_data.get("state", "")
                    message = status_data.get("message", "")

                    if state == "Finished":
                        return "Finished"
                    elif state == "Failed":
                        print(f"   ❌ Download error: {message}")
                        return f"Failed: {message}"

            except Exception as e:
                print(f"   ⚠ Check status error: {e}")

            time.sleep(wait_interval)
            elapsed_time += wait_interval

        return "Timeout"


class CvatUploader(CvatCore):
    def __init__(self, cvat_credentials_path: str, table_url: str | None = None, table_credentials_path: str | None = None):
        """
        CVAT uploader class for uploading data to CVAT.

        Parameters
        ----------
        cvat_credentials_path : str
            Path to YAML file with CVAT credentials
        table_url: str | None
            Url of google table
        table_credentials_path: str | None
            Private data for work with table

        """
        super().__init__(cvat_credentials_path)

        self.table_editor = None
        if table_url is not None and table_credentials_path is not None:
            self.table_editor = TableEditor(table_url, table_credentials_path)


    def write_data_to_table(self, data_dict: dict, worksheet_name: int = 0):
        """
        Add data to table for target columns.
        
        Parameters
        ----------
        data_dict : dict
            Example: {'column name': 'value', ...}
        worksheet_name : int
            Sheet id in target table
        """
        worksheet = self.table_editor.sheet.get_worksheet(worksheet_name)
        
        try:
            all_data = worksheet.get_all_values()
            
            if not all_data:
                raise ValueError("Table is empty!")
            
            headers = all_data[0]
            
            new_row = [""] * len(headers)
            
            for column_name, value in data_dict.items():
                if column_name in headers:
                    column_index = headers.index(column_name)
                    new_row[column_index] = str(value) if value is not None else ""
                else:
                    print(f"⚠️ Column'{column_name}' does not find! Excists columns: {headers}")
            
            worksheet.append_row(new_row)
            
            print(f"✅ Succes added data:")
            for column_name, value in data_dict.items():
                if column_name in headers:
                    print(f"   📌 {column_name}: {value}")
            
        except Exception as e:
            print(f"❌ Add data error: {e}")


    def upload_from_share_folders(
        self, 
        project_id: int, 
        share_path: str,
        directory_names: list[str] | None = None,
        column_names: list[str] | None = None,
        sheet_id: int | None = None
    ):
        """
        Upload data from share to CVAT.

        Parameters
        ----------
        project_id : int
            ID of the project
        share_path : str
            Path to data on CVAT share
        directory_names : Optional[list[str]], optional
            List of directory names to upload. If None, upload all directories, by default None
        column_names: list[str] | None
            Names of target columns in table
        sheet_id: int | None
            Id of sheet in target table
        """
        session = self._create_session()

        print("Start upload data from CVAT share...")
        print("=" * 60)

        try:
            if directory_names is None:
                directories = self._get_share_directories(share_path)
                if not directories:
                    print("❌ No directories found to upload")
                    return
            else:
                directories = directory_names

            print(f"Processing {len(directories)} directories...")

            for dir_name in directories:
                print(f"\nStart job with directory: {dir_name}")
                print("-" * 40)

                if self._is_task_exists(session, dir_name, project_id):
                    print(f"⚠ Task '{dir_name}' already exists in project {project_id}. Skipping...")
                    continue

                full_share_path = f"{share_path}/{dir_name}"

                try:
                    task_payload = {"name": dir_name, "project_id": project_id}
                    create_response = session.post(
                        f"{self.base_url}/api/tasks", 
                        json=task_payload, 
                        timeout=30
                    )

                    if create_response.status_code not in [200, 201]:
                        print(f"❌ Create task error: {create_response.text}")
                        continue

                    task_data = create_response.json()

                    task_id = task_data["id"]

                    print(f"Task is created: {dir_name} (ID: {task_id})...✅")

                    share_data = {
                        "server_files": [f"{full_share_path}/"],
                        "image_quality": 100,
                        "use_zip_chunks": False,
                        "sorting_method": "natural",
                    }

                    print(f"Download data from: {full_share_path}")
                    upload_response = session.post(
                        f"{self.base_url}/api/tasks/{task_id}/data", 
                        json=share_data, 
                        timeout=30
                    )

                    print(f"   Download status: {upload_response.status_code}")

                    if upload_response.status_code in [200, 202]:
                        print("Request is accepted...✅")

                        task_status = self.wait_for_load_completion(session=session, task_id=task_id)

                        if task_status == "Finished":

                            if self.table_editor is not None:

                                task_info_response = session.get(f"{self.base_url}/api/tasks/{task_id}")
                                if task_info_response.status_code == 200:
                                    task_info = task_info_response.json()
                                    
                                    task_url = f"{self.base_url}/tasks/{task_id}"
                                    image_count = task_info.get("size", 0)

                                    data_dict = dict(zip(column_names, [task_url, image_count]))
                                    
                                    print(f"   📊 Task Info:")
                                    print(f"   URL: {task_url}")
                                    print(f"   Images: {image_count}")

                                    self.write_data_to_table(data_dict=data_dict, worksheet_name=sheet_id)

                            print(f"{dir_name} - Success...✅")
                        else:
                            self._cleanup_task(session, task_id, f"Upload failed: {task_status}")
                    else:
                        print(f"❌ Download error: {upload_response.text}")
                        self._cleanup_task(session, task_id, "Upload request failed")

                except Exception as e:
                    print(f"❌ Error with directory {dir_name}: {e}")
                    if 'task_id' in locals():
                        self._cleanup_task(session, task_id, f"Exception: {str(e)}")

        except Exception as e:
            print(f"❌ Error during upload process: {e}")
        
        finally:
            session.close()

    def _is_task_exists(self, session: requests.Session, task_name: str, project_id: int) -> bool:
        """
        Check if task with given name already exists in the project.

        Parameters
        ----------
        session : requests.Session
            Active session
        task_name : str
            Name of the task to check
        project_id : int
            ID of the project to check in

        Returns
        -------
        bool
            True if task exists, False otherwise
        """
        try:
            tasks_response = session.get(
                f"{self.base_url}/api/tasks?project_id={project_id}",
                timeout=30
            )

            if tasks_response.status_code == 200:
                tasks_data = tasks_response.json()
                
                if isinstance(tasks_data, dict) and 'results' in tasks_data:
                    tasks_list = tasks_data['results']
                elif isinstance(tasks_data, list):
                    tasks_list = tasks_data
                else:
                    tasks_list = []
                
                for task in tasks_list:
                    if task.get('name') == task_name:
                        return True
            
            return False
            
        except Exception as e:
            print(f"⚠ Error checking if task exists: {e}")
            return False

    def _cleanup_task(self, session: requests.Session, task_id: int, reason: str):
        """
        Clean up task in case of error.

        Parameters
        ----------
        session : requests.Session
            Active session
        task_id : int
            ID of task to delete
        reason : str
            Reason for cleanup
        """
        try:
            session.delete(f"{self.base_url}/api/tasks/{task_id}")
            print(f"Task {task_id} has been deleted ({reason})")
        except Exception as e:
            print(f"Warning: Could not delete task {task_id}: {e}")