import time
from typing import Optional, Any
from pathlib import Path

import requests
import yaml
import pandas as pd
import json
from dataclasses import dataclass

from src.cascade.tables.table import TableEditor


@dataclass
class DownloadResult:
    """Result of download operation."""
    success: bool
    file_path: Optional[str] = None
    is_error: bool = False
    error_message: Optional[str] = None


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
                if dir_name[-1] == '\n':
                    dir_name = dir_name[:-1]
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


class CvatDownloader(CvatCore):
    def __init__(self, cvat_credentials_path: str, table_url: str | None = None, table_credentials_path: str | None = None):
        """
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

    def export_tasks(
    self,
    project_id: int,
    export_format: str,
    task_ids: Optional[list[int]],
    output_dir: str,
    include_images: bool = True
    ) -> dict[str, Any]:
        """
        Export tasks from CVAT project.

        Parameters
        ----------
        project_id : int
            ID of the project to export from
        export_format : str
            Export format (YOLO 1.1, COCO 1.0, VOC 1.1, etc.)
        task_ids : Optional[list[int]]
            List of specific task IDs to export. If None, export all tasks
        output_dir : str
            Local directory to save exported files
        include_images : bool, optional
            Whether to include images in export, by default True

        Returns
        -------
        dict[str, Any]
            Export results with file paths and statuses
        """
        session = self._create_session()
        Path(output_dir).mkdir(exist_ok=True)
        
        print("Starting CVAT export...")
        print("=" * 60)
        
        tasks_to_export = self._get_tasks_for_export(session, project_id, task_ids)
        
        if not tasks_to_export:
            print("❌ No tasks found to export")
            return {}
        
        print(f"Found {len(tasks_to_export)} tasks to export")
        
        results = {}
        
        for task in tasks_to_export:
            task_id = task['id']
            task_name = task['name']
            
            print(f"\nExporting: {task_name} (ID: {task_id})")
            
            try:
                local_path = self._start_export(
                    session=session,
                    task_id=task_id,
                    task_name=task_name,
                    output_dir=output_dir,
                    export_format=export_format,
                    include_images=include_images
                )
                
                if local_path:
                    results[task_id] = {
                        "status": "success",
                        "task_name": task_name,
                        "local_path": local_path
                    }
                    print(f"✅ Success: {local_path}")
                else:
                    results[task_id] = {
                        "status": "failed", 
                        "task_name": task_name,
                        "error": "Export failed"
                    }
                    print(f"❌ Export failed for {task_name}")
                    
            except Exception as e:
                results[task_id] = {
                    "status": "error",
                    "task_name": task_name, 
                    "error": str(e)
                }
                print(f"❌ Error exporting {task_name}: {e}")
        
        print(f"\nExport completed: {len([r for r in results.values() if r['status'] == 'success'])}/{len(results)} successful")
        return results

    def _get_tasks_for_export(
        self,
        session: requests.Session, 
        project_id: int, 
        task_ids: Optional[list[int]] = None
    ) -> list[dict]:
        """
        Get list of tasks to export.
        
        Parameters
        ----------
        session : requests.Session
            Authenticated session
        project_id : int
            ID of the project
        task_ids : Optional[list[int]]
            List of specific task IDs to export
        
        Returns
        -------
        list[dict]
            List of task dictionaries
        """
        all_tasks = self._get_all_tasks(session, project_id)
        
        if task_ids is None:
            return all_tasks
        else:
            return [task for task in all_tasks if int(task['id']) in task_ids]

    def _get_all_tasks(self, session: requests.Session, project_id: int) -> list[dict]:
        """
        Get all tasks from project with pagination.
        
        Parameters
        ----------
        session : requests.Session
            Authenticated session
        project_id : int
            ID of the project
        
        Returns
        -------
        list[dict]
            List of all task dictionaries
        """
        all_tasks = []
        page = 1
        
        while True:
            response = session.get(
                f"{self.base_url}/api/tasks",
                params={"project_id": project_id, "page": page, "page_size": 100}
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            
            if isinstance(data, dict) and 'results' in data:
                tasks = data['results']
                all_tasks.extend(tasks)
                
                if not data.get('next'):
                    break
            elif isinstance(data, list):
                all_tasks.extend(data)
                break
            else:
                break
                
            page += 1
            
        return all_tasks

    def _start_export(
        self,
        session: requests.Session,
        task_id: int,
        task_name: str,
        output_dir: str,
        export_format: str,
        include_images: bool = True
    ) -> Optional[str]:
        """
        Start export process and download the file.
        
        Parameters
        ----------
        session : requests.Session
            Authenticated session
        task_id : int
            ID of the task to export
        task_name : str
            Name of the task
        output_dir : str
            Local directory to save exported file
        export_format : str
            Export format
        include_images : bool, optional
            Whether to include images, by default True
        
        Returns
        -------
        Optional[str]
            Local path to downloaded file or None if failed
        """
        export_params = {
            "format": export_format,
            "filename": f"task_{task_id}_export",
        }
        
        if not include_images:
            export_params["image_quality"] = 0
            
        print(f"   Starting export...")
        export_response = session.get(
            f"{self.base_url}/api/tasks/{task_id}/annotations",
            params=export_params
        )
        
        print(f"   Export init: {export_response.status_code}")
        
        if export_response.status_code in [201, 202]:
            return self._wait_for_export_ready(
                session=session,
                task_id=task_id,
                task_name=task_name,
                export_format=export_format,
                output_dir=output_dir
            )
        else:
            print(f"   ❌ Export init failed: {export_response.text}")
            return None

    def _wait_for_export_ready(
    self, 
    session: requests.Session, 
    task_id: int,
    task_name: str,
    export_format: str,
    output_dir: str,
    max_wait: int = 300
    ) -> Optional[str]:
        """
        Wait for export to be ready and download the file.
        
        Parameters
        ----------
        session : requests.Session
            Authenticated session
        task_id : int
            ID of the task
        task_name : str
            Name of the task
        export_format : str
            Export format
        output_dir : str
            Local directory to save file
        max_wait : int, optional
            Maximum wait time in seconds, by default 300
        
        Returns
        -------
        Optional[str]
            Local path to downloaded file or None if failed
        """
        print(f"   Waiting for export ({max_wait}s max)...")
        
        for i in range(max_wait // 10):
            time.sleep(10)
            
            download_result = self._download_export_file(
                session=session,
                task_id=task_id,
                task_name=task_name,
                export_format=export_format,
                output_dir=output_dir
            )
            
            if download_result.success:
                print(f"      ✅ Export completed and downloaded!")
                return download_result.file_path
            elif download_result.is_error:
                print(f"      ❌ Download error: {download_result.error_message}")
                return None
            else:
                print(f"      Download check {i+1}: file not ready yet")
        
        print(f"      ⚠ Export timeout after {max_wait}s")
        return None

    def _download_export_file(
        self,
        session: requests.Session,
        task_id: int,
        task_name: str,
        export_format: str,
        output_dir: str
    ) -> DownloadResult:
        """
        Download exported file to local directory.
        
        Parameters
        ----------
        session : requests.Session
            Authenticated session
        task_id : int
            ID of the task
        task_name : str
            Name of the task
        export_format : str
            Export format
        output_dir : str
            Local directory to save file
        
        Returns
        -------
        DownloadResult
            Result object with status and file path
        """
        download_response = session.get(
            f"{self.base_url}/api/tasks/{task_id}/annotations", 
            params={
                "format": export_format,
                "action": "download"
            }
        )
        
        if download_response.status_code == 200:
            content_type = download_response.headers.get('content-type', '')
            
            if 'application/zip' in content_type or 'octet-stream' in content_type:
                safe_task_name = "".join(c for c in task_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"{safe_task_name}.zip"
                local_path = Path(output_dir) / filename

                with open(local_path, 'wb') as f:
                    f.write(download_response.content)
                
                file_size = local_path.stat().st_size
                print(f"      ✅ File saved: {local_path.name} ({file_size / 1024 / 1024:.1f} MB)")
                return DownloadResult(success=True, file_path=str(local_path))
            else:
                error_msg = f"Unexpected content type: {content_type}"
                print(f"      ❌ {error_msg}")
                return DownloadResult(success=False, is_error=True, error_message=error_msg)
        elif download_response.status_code == 202:
            return DownloadResult(success=False, is_error=False)
        else:
            error_msg = f"Download failed with status: {download_response.status_code}"
            print(f"      ❌ {error_msg}")
            return DownloadResult(success=False, is_error=True, error_message=error_msg)