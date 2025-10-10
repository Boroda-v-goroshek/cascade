from pathlib import Path
import os
import yaml
import re
from typing import Optional
from dataclasses import dataclass

from jsonargparse import CLI
import pandas as pd

from src.cascade.tables.table import TableEditor
from src.cascade.cvat.cvat_core import CvatDownloader
from salary_for_annotation import BoxCostsConfig, CostsParamsConfig, count_salary

NAME_OF_DATE_COLUMN = "Целевая дата выплаты"


@dataclass
class TaskData:
    url: str
    project_id: int
    task_id: int
    task_name: str
    frames: Optional[str]
    increase_price_frames: Optional[int]
    assigner: str
    frames_count: int
    local_path: Optional[str] = None
    have_preannotated: bool = True


PROJECT_NAMES = {
    35: 'fsra_35',
    29: 'drone_detection_29', 
    26: 'building_machines_26',
    25: 'building_machines_orlovka_25'
}


def extract_task_id_from_url(job_url: str) -> int:
    """Extract task ID from CVAT job URL."""
    match = re.search(r'/tasks/(\d+)', job_url)
    if match:
        return int(match.group(1))
    raise ValueError(f"Cannot extract task ID from URL: {job_url}")


def get_project_name(project_id: int) -> Optional[str]:
    """Get project name by ID."""
    return PROJECT_NAMES.get(project_id)


def write_in_salary_table(table_url: str, table_credentials_path: str, data: list[str]):
    """
    Write data to salary table.
    
    Parameters
    ----------
    table_url : str
        URL of the Google Sheets table
    table_credentials_path : str
        Path to Google Sheets credentials
    data : list[str]
        List of values to write
    """
    table_editor = TableEditor(table_url, table_credentials_path)    
    table_editor.append_to_end([data])


def _process_table_sheet(table_editor: TableEditor, sheet_id: int, date: str) -> list[TaskData]:
    """Process a single sheet and extract TaskData."""
    try:
        df = table_editor.get_named_table(sheet_id)
        
        if NAME_OF_DATE_COLUMN not in df.columns:
            print(f"Sheet {sheet_id}: no date column, skipping")
            return []
            
        filtered_df = df[df[NAME_OF_DATE_COLUMN] == date]
        
        if filtered_df.empty:
            print(f"Sheet {sheet_id}: no tasks for date {date}")
            return []
        
        tasks = []
        for _, row in filtered_df.iterrows():
            try:
                increase_price_frames = row.get('Картинки по повышенной цене')
                if increase_price_frames not in [None, '']:
                    try:
                        increase_price_frames = int(float(increase_price_frames)) if increase_price_frames else None
                    except (ValueError, TypeError):
                        increase_price_frames = None
                        print(f"⚠️  Invalid increase_price_frames value in sheet {sheet_id}")

                task_data = TaskData(
                    url=str(row['Ссылка на джобу']),
                    task_id=extract_task_id_from_url(str(row['Ссылка на джобу'])),
                    task_name="",
                    project_id=int(row['ID проекта']),
                    frames_count=int(row.get("Кол-во картинок", 0)),
                    assigner=row.get("Исполнитель", ""),
                    frames=row.get('Кадры'),
                    increase_price_frames=increase_price_frames,
                    have_preannotated=row.get('Есть предразметка') != 'нет'
                )
                tasks.append(task_data)
            except (ValueError, KeyError) as e:
                print(f"Error processing row: {e}")
                continue
                
        return tasks
        
    except Exception as e:
        print(f"Error processing sheet {sheet_id}: {e}")
        return []


def parse_annotations_table(
    table_url: str, 
    table_credentials_path: str, 
    date: str
) -> list[TaskData]:
    """Parse table and return list of TaskData objects."""
    table_editor = TableEditor(table_url, table_credentials_path)
    all_tasks = []
    
    try:
        num_sheets = table_editor.get_sheet_count()
        print(f"📊 Found {num_sheets} sheets to process")
        
        for sheet_id in range(num_sheets):
            sheet_tasks = _process_table_sheet(table_editor, sheet_id, date)
            all_tasks.extend(sheet_tasks)
            
    except Exception as e:
        print(f"❌ Error getting sheet count: {e}")
        print("🔄 Using iterative approach as fallback")
        sheet_id = 0
        max_sheets = 10
        
        while sheet_id < max_sheets:
            sheet_tasks = _process_table_sheet(table_editor, sheet_id, date)
            if not sheet_tasks and sheet_id > 10:
                break
            all_tasks.extend(sheet_tasks)
            sheet_id += 1
    
    print(f"✅ Processed sheets, found {len(all_tasks)} tasks total")
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
    
    return {
        task_id: (result["task_name"], result["local_path"])
        for task_id, result in results.items()
        if result["status"] == "success"
    }


def _find_deepest_directory(current_path: Path, max_depth_path: Path, max_depth: int) -> tuple[Path, int]:
    """Recursively find the deepest directory in the path."""
    try:
        subdirs = [item for item in current_path.iterdir() if item.is_dir()]
    except PermissionError:
        return max_depth_path, max_depth
    
    if not subdirs:
        current_depth = len(current_path.parts)
        if current_depth > max_depth:
            return current_path, current_depth
        return max_depth_path, max_depth
    
    for subdir in subdirs:
        max_depth_path, max_depth = _find_deepest_directory(subdir, max_depth_path, max_depth)
    
    return max_depth_path, max_depth


def get_valid_path_to_labels(path: str) -> str:
    """
    Find directory that contains both images and text files directly.
    
    Parameters
    ----------
    path: str
        Starting path to search from
        
    Returns
    -------
    str
        Path to valid directory with mixed files
    """
    path_obj = Path(path)
    
    if not path_obj.exists() or not path_obj.is_dir():
        raise ValueError(f"Path '{path}' does not exist or is not a directory")
    
    deepest_path, _ = _find_deepest_directory(path_obj, path_obj, len(path_obj.parts))
    return str(deepest_path)


def _parse_frames_range(frames: Optional[str]) -> tuple[int, int]:
    """Parse frames range string into from and to values."""
    if not frames:
        return 0, -1
    
    frames_range_formatted = frames.strip().split('-')
    if len(frames_range_formatted) == 2:
        return int(frames_range_formatted[0]), int(frames_range_formatted[1])
    
    return 0, -1


def process_of_count_salary(
    initial_labels_path: str, 
    final_labels_path: str, 
    frames_from: int,
    frames_to: int, 
    increase_price_frames: Optional[int],
    cost_diff_box: int,
    cost_diff_box_increased: int,
    cost_new_box: int,
    cost_new_box_increased: int,
    box_change_low_threshold: int,
    box_change_high_threshold: int,
    have_preannotated: bool
):
    """Calculate salary for annotation work."""
    initial_labels_path = get_valid_path_to_labels(initial_labels_path)
    final_labels_path = get_valid_path_to_labels(final_labels_path)

    increased_cost_frame_from = frames_from if increase_price_frames else -1
    increased_cost_frame_to = (frames_from + increase_price_frames) if increase_price_frames else -1

    box_costs_cfg = BoxCostsConfig(
        cost_diff_box=cost_diff_box,
        cost_diff_box_increased=cost_diff_box_increased,
        cost_new_box=cost_new_box,
        cost_new_box_increased=cost_new_box_increased,
    )

    costs_params_cfg = CostsParamsConfig(
        initial_labels_path=Path(initial_labels_path),
        final_labels_path=Path(final_labels_path),
        box_costs_cfg=box_costs_cfg,
        box_change_low_threshold=box_change_low_threshold,
        box_change_high_threshold=box_change_high_threshold,
        increased_cost_frame_from=increased_cost_frame_from,
        increased_cost_frame_to=increased_cost_frame_to,
        frames_from=frames_from,
        frames_to=frames_to,
        have_preannotated=have_preannotated
    )

    return count_salary(costs_params_cfg=costs_params_cfg)


def _process_single_task(
    task_data: TaskData,
    project_name: str,
    cost_config: dict,
    salary_table_url: str,
    table_credentials_path: str
):
    """Process a single task and calculate salary."""
    if not task_data.local_path:
        return

    task_name = task_data.task_name
    initial_labels_path = f"/mnt/cvat_share/{project_name}/{task_name}"

    # Clean up None values
    frames = task_data.frames if task_data.frames != '' else None
    increase_price_frames = task_data.increase_price_frames if task_data.increase_price_frames != '' else None

    frames_from, frames_to = _parse_frames_range(frames)

    try:
        salary_data = process_of_count_salary(
            initial_labels_path=initial_labels_path,
            final_labels_path=task_data.local_path,
            frames_from=frames_from,
            frames_to=frames_to,
            increase_price_frames=increase_price_frames,
            **cost_config,
            have_preannotated=task_data.have_preannotated
        )
        
        salary, new_boxes, deleted_boxes, diff_class_boxes, diff_boxes = salary_data
        
        frames_processed = frames_to - frames_from if frames_to != -1 else task_data.frames_count
        
        data_for_salary_table = [
            task_data.url,
            task_data.assigner,
            str(deleted_boxes), 
            str(new_boxes), 
            str(diff_class_boxes), 
            str(diff_boxes), 
            str(task_data.frames_count), 
            str(frames_processed), 
            str(frames_from),
            str(increase_price_frames) if increase_price_frames else "",
            str(round(salary, 2)),
            ""
        ]

        write_in_salary_table(salary_table_url, table_credentials_path, data_for_salary_table)

    except Exception as e:
        print(f"❌ Salary calculation failed for {task_data.task_name}: {e}")


def _group_tasks_by_project(task_data_list: list[TaskData]) -> dict[int, list[TaskData]]:
    """Group tasks by project ID."""
    tasks_by_project = {}
    for task_data in task_data_list:
        if task_data.project_id not in tasks_by_project:
            tasks_by_project[task_data.project_id] = []
        tasks_by_project[task_data.project_id].append(task_data)
    return tasks_by_project


def main(args_path: str | Path):
    """Main function."""
    with open(args_path, "r", encoding="utf-8") as file:
        args = yaml.safe_load(file)
    
    # Extract configuration
    config = {
        'table_url': args["table_url"],
        'table_credentials_path': args["table_credentials_path"],
        'date': args["date"],
        'output_dir': args['output_dir'],
        'cvat_credentials_path': args["cvat_credentials_path"],
        'export_format': args["export_format"],
        'include_images': args["include_images"],
        'salary_table_url': args["salary_table_url"]
    }
    
    cost_config = {
        'cost_diff_box': args["cost_diff_box"],
        'cost_diff_box_increased': args["cost_diff_box_increased"],
        'cost_new_box': args["cost_new_box"],
        'cost_new_box_increased': args["cost_new_box_increased"],
        'box_change_low_threshold': args["box_change_low_threshold"],
        'box_change_high_threshold': args["box_change_high_threshold"]
    }
    
    # Parse tasks
    task_data_list = parse_annotations_table(
        table_url=config['table_url'],
        table_credentials_path=config['table_credentials_path'],
        date=config['date']
    )
    
    if not task_data_list:
        print("❌ No tasks found for the specified date")
        return
    
    print(f"✅ Found {len(task_data_list)} tasks for date {config['date']}")
    
    # Process by project
    tasks_by_project = _group_tasks_by_project(task_data_list)
    
    for project_id, project_tasks in tasks_by_project.items():
        project_name = get_project_name(project_id)
        print(f"\nProcessing project {project_name} with {len(project_tasks)} tasks...")
        
        project_output_dir = f"{config['output_dir']}/{project_id}"
        
        # Download tasks
        task_mapping = process_of_download(
            cvat_credentials_path=config['cvat_credentials_path'],
            project_id=project_id,
            task_data_list=project_tasks,
            output_dir=project_output_dir,
            export_format=config['export_format'],
            include_images=config['include_images']
        )
        
        # Update task data with download results
        for task_data in project_tasks:
            if task_data.task_id in task_mapping:
                task_name, local_path = task_mapping[task_data.task_id]
                task_data.task_name = task_name
                task_data.local_path = local_path
        
        # Process each task
        for task_data in project_tasks:
            _process_single_task(
                task_data=task_data,
                project_name=project_name,
                cost_config=cost_config,
                salary_table_url=config['salary_table_url'],
                table_credentials_path=config['table_credentials_path']
            )


if __name__ == "__main__":
    CLI(main, as_positional=False)