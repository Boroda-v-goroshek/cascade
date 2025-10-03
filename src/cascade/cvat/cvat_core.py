import time

import requests
import yaml


class CvatCore:
    def __init__(self, credentials_path: str):
        self.get_cvat_data(credentials_path)
        # self.upload_table_data = (table_url, sheet_id)

    def get_cvat_data(self, path_to_yml: str) -> tuple[str, str, str]:
        """
        Download credentials data from yml.

        Parameters
        ----------
        path_to_yml: str
            Path to credentials file

        Returns
        -------
        tuple[str, str, str]
            Server url, username and password

        """
        if path_to_yml:
            with open(path_to_yml, "r", encoding="utf-8") as file:
                args = yaml.safe_load(file)
        else:
            raise ValueError("path_to_yml is empty or invalid")

        self.base_url = args["base_url"]
        self.username = args["username"]
        self.password = args["password"]

        return self.base_url, self.username, self.password

    def write_data_for_table(data: list[str]):  # type: ignore
        pass

    def upload_from_share_folders(self, directory_names: list[str], project_id: int, share_path: str):
        """
        Upload data from share to CVAT (all data in directory_names).

        Parameters
        ----------
        directory_names: list[str]
            List with name of dir you need
        prject_id: int
            Name of project
        share_path: str
            Path to data on CVAT share

        """
        session = requests.Session()

        print("Start upload data from CVAT share...")
        print("=" * 60)

        print("1. Logining...")
        try:
            login_response = session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=30,
            )

            if login_response.status_code != 200:
                print(f"❌ Login error: {login_response.text}")
                return []

            auth_data = login_response.json()
            session.headers.update({"Authorization": f"Token {auth_data['key']}"})
            print("Success...✅")

        except Exception as e:
            print(f"❌ Login error: {e}")
            return []

        for dir_name in directory_names:
            print(f"\nStart job with directory: {dir_name}")
            print("-" * 40)

            share_path = f"{share_path}/{dir_name}"

            try:
                task_payload = {"name": dir_name, "project_id": project_id}

                create_response = session.post(f"{self.base_url}/api/tasks", json=task_payload, timeout=30)

                if create_response.status_code not in [200, 201]:
                    print(f"❌ Create task error: {create_response.text}")
                    continue

                task_data = create_response.json()
                task_id = task_data["id"]
                print(f"Task is created: {dir_name} (ID: {task_id})...✅")

                share_data = {
                    "server_files": [f"{share_path}/"],
                    "image_quality": 100,
                    "use_zip_chunks": False,
                    "sorting_method": "natural",
                }

                print(f"Download data from: {share_path}")
                upload_response = session.post(f"{self.base_url}/api/tasks/{task_id}/data", json=share_data, timeout=30)

                print(f"   Download status: {upload_response.status_code}")

                if upload_response.status_code in [200, 202]:
                    print("Request is accepted...✅")

                    task_status = self.wait_for_upload_completion(session=session, task_id=task_id)

                    if task_status == "Finished":
                        print(f"{dir_name} - Success...✅")
                    else:
                        try:
                            session.delete(f"{self.base_url}/api/tasks/{task_id}")
                            print(f"Task {task_id} has been deleted")
                        except:
                            pass
                else:
                    print(f"❌ Download error: {upload_response.text}")
                    try:
                        session.delete(f"{self.base_url}/api/tasks/{task_id}")
                    except:
                        pass

            except Exception as e:
                print(f"❌ Error with directory: {dir_name}: {e}")

    def upload_from_share_folders_all(self, project_id: int, share_path: str):
        """
        Upload data from share to CVAT (all directories in share_path).

        Parameters
        ----------
        prject_id: int
            Name of project
        share_path: str
            Path to data on CVAT share

        """
        session = requests.Session()

        print("Start upload data from CVAT share...")
        print("=" * 60)

        print("1. Logining...")
        try:
            login_response = session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=30,
            )

            if login_response.status_code != 200:
                print(f"❌ Login error: {login_response.text}")
                return []

            auth_data = login_response.json()
            session.headers.update({"Authorization": f"Token {auth_data['key']}"})
            print("Success...✅")

        except Exception as e:
            print(f"❌ Login error: {e}")
            return []

        try:
            share_list_response = session.get(f"{self.base_url}/api/server/share?directory={share_path}", timeout=30)

            if share_list_response.status_code == 200:
                share_data = share_list_response.json()
                directories = []
                for item in share_data:
                    if item.get("type") == "DIR":
                        directories.append(item.get("name", ""))

                print(f"Found {len(directories)} directories in {share_path}")
            else:
                print("❌ Cannot get directory list from share!")
                directories = []

        except Exception as e:
            print(f"❌ Error getting directory list: {e}")
            directories = []

        for dir_name in directories:
            print(f"\nStart job with directory: {dir_name}")
            print("-" * 40)

            full_share_path = f"{share_path}/{dir_name}"

            try:
                task_payload = {"name": dir_name, "project_id": project_id}

                create_response = session.post(f"{self.base_url}/api/tasks", json=task_payload, timeout=30)

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
                upload_response = session.post(f"{self.base_url}/api/tasks/{task_id}/data", json=share_data, timeout=30)

                print(f"   Download status: {upload_response.status_code}")

                if upload_response.status_code in [200, 202]:
                    print("Request is accepted...✅")

                    task_status = self.wait_for_upload_completion(session=session, task_id=task_id)

                    if task_status == "Finished":
                        print(f"{dir_name} - Success...✅")
                    else:
                        try:
                            session.delete(f"{self.base_url}/api/tasks/{task_id}")
                            print(f"Task {task_id} has been deleted")
                        except:
                            pass
                else:
                    print(f"❌ Download error: {upload_response.text}")
                    try:
                        session.delete(f"{self.base_url}/api/tasks/{task_id}")
                    except:
                        pass

            except Exception as e:
                print(f"❌ Error with directory: {dir_name}: {e}")

    def wait_for_upload_completion(self, session: requests.Session, task_id: int, max_wait: int = 300) -> str:
        """
        Waiting download data to task.

        Parameters
        ----------
        session: requests.Session
            Active session
        task_id: int
            ID for target task
        max_wait: int
            Max time (seconds) for waiting download

        Returns
        -------
        str
            Status for uploading process or error message

        """
        wait_interval = 5
        elapsed_time = 0

        while elapsed_time < max_wait:
            try:
                status_response = session.get(f"{self.base_url}/api/tasks/{task_id}/status", timeout=10)

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
                print(f"   ⚠ Checked status error: {e}")

            time.sleep(wait_interval)
            elapsed_time += wait_interval

        return "Timeout"
