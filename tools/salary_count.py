from pathlib import Path
import yaml
from typing import Optional

from jsonargparse import CLI
import pandas as pd
from dataclasses import dataclass

from src.cascade.tables.table import TableEditor
from src.cascade.tools.data_transfer import DataTransfer
from src.cascade.cvat.cvat_core import CvatDownloader

NAME_OF_DATE_COLUMN = "Целевая дата выплаты"


@dataclass
class TaskData:
    url: str
    project_id: int
    task_id: int
    task_name: str
    frames: Optional[str]
    increase_price_frames: Optional[int]
    local_path: Optional[str] = None


def extract_task_id_from_url(job_url: str) -> int:
    """Extract task ID from CVAT job URL."""
    import re
    match = re.search(r'/tasks/(\d+)', job_url)
    if match:
        return int(match.group(1))
    raise ValueError(f"Cannot extract task ID from URL: {job_url}")


def parse_annotations_table(
    table_url: str, 
    table_credentials_path: str, 
    date: str
) -> list[TaskData]:
    """Parse table and return list of TaskData objects."""
    table_editor = TableEditor(table_url, table_credentials_path)
    all_tasks = []
    
    sheet_id = 0
    while True:
        try:
            df = table_editor.get_named_table(sheet_id)
            
            if NAME_OF_DATE_COLUMN not in df.columns:
                print(f"Sheet {sheet_id}: no date column, skipping")
                sheet_id += 1
                continue
                
            filtered_df = df[df[NAME_OF_DATE_COLUMN] == date]
            
            if filtered_df.empty:
                print(f"Sheet {sheet_id}: no tasks for date {date}")
                sheet_id += 1
                continue
            
            for _, row in filtered_df.iterrows():
                try:
                    task_data = TaskData(
                        url=str(row['Ссылка на джобу']),
                        task_id=extract_task_id_from_url(str(row['Ссылка на джобу'])),
                        task_name="",
                        project_id=int(row['ID проекта']),
                        frames=row.get('Кадры'),
                        increase_price_frames=row.get('Картинки по повышенной цене')
                    )
                    all_tasks.append(task_data)
                except (ValueError, KeyError) as e:
                    print(f"Error processing row: {e}")
                    continue
                    
            sheet_id += 1
            
        except Exception as e:
            print(f"No more sheets or error: {e}")
            break
    
    return all_tasks


def process_of_download(
    cvat_credentials_path: str, 
    project_id: int, 
    task_data_list: list[TaskData],
    output_dir: str = "./exports",
    export_format: str = "YOLO 1.1",
    include_images: bool = False
) -> dict[int, tuple[str, str]]:
    """Download tasks and return mapping with task names and paths."""
    cvat_downloader = CvatDownloader(cvat_credentials_path)
    
    task_ids = [task.task_id for task in task_data_list]
    
    results = cvat_downloader.export_tasks(
        project_id=project_id,
        export_format=export_format,
        task_ids=task_ids,
        output_dir=output_dir,
        include_images=include_images
    )
    
    task_mapping = {}
    for task_id, result in results.items():
        if result["status"] == "success":
            task_mapping[task_id] = (result["task_name"], result["local_path"])
    
    return task_mapping


def count_salary():
    pass


def main(args_path: str | Path):
    """Main function."""
    with open(args_path, "r", encoding="utf-8") as file:
        args = yaml.safe_load(file)
    
    task_data_list = parse_annotations_table(
        table_url=args["table_url"],
        table_credentials_path=args["table_credentials_path"],
        date=args["date"]
    )
    
    if not task_data_list:
        print("❌ No tasks found for the specified date")
        return
    
    print(f"✅ Found {len(task_data_list)} tasks for date {args['date']}")
    
    tasks_by_project = {}
    for task_data in task_data_list:
        if task_data.project_id not in tasks_by_project:
            tasks_by_project[task_data.project_id] = []
        tasks_by_project[task_data.project_id].append(task_data)
    
    for project_id, project_tasks in tasks_by_project.items():
        print(f"\nProcessing project {project_id} with {len(project_tasks)} tasks...")
        
        output_dir = f"{args['output_dir']}/{project_id}"
        
        task_mapping = process_of_download(
            cvat_credentials_path=args["cvat_credentials_path"],
            project_id=project_id,
            task_data_list=project_tasks,
            output_dir=output_dir,
            export_format=args["export_format"],
            include_images=args["include_images"]
        )
        
        for task_data in project_tasks:
            if task_data.task_id in task_mapping:
                task_name, local_path = task_mapping[task_data.task_id]
                task_data.task_name = task_name
                task_data.local_path = local_path
        
        for task_data in project_tasks:
            if task_data.local_path:
                try:
                    salary_data = count_salary(
                        task_name=task_data.task_name,
                        frames_range=task_data.frames,  # Может быть None
                        increase_price_frames=task_data.increase_price_frames  # Может быть None
                    )
                    print(f"✅ Salary for {task_data.task_name}: {salary_data}")
                except Exception as e:
                    print(f"❌ Salary calculation failed for {task_data.task_name}: {e}")

if __name__ == "__main__":
    CLI(main, as_positional=False)