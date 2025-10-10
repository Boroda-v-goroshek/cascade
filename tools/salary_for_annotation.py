"""Count salary for annotations with increased costs."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonargparse import CLI
from tqdm import tqdm


@dataclass
class BoxCostsConfig:
    """Config thath stores costs of new and changed boxes."""

    cost_diff_box: float = 0.4
    cost_diff_box_increased: float = 0.6
    cost_new_box: float = 0.8
    cost_new_box_increased: float = 1


@dataclass
class CostsParamsConfig:
    """Config that stores all parameters."""

    initial_labels_path: Path
    final_labels_path: Path
    box_costs_cfg: BoxCostsConfig
    box_change_low_threshold: float = 0.1
    box_change_high_threshold: float = 0.7
    increased_cost_frame_from: int = -1
    increased_cost_frame_to: int = -1
    frames_from: int = 0
    frames_to: int = -1
    have_preannotated: bool = True


@dataclass
class BBox:
    """Bounding box."""

    obj_class: float
    x_center: float
    y_center: float
    width: float
    height: float


@dataclass
class BoxCounts:
    """Contains boundig boxes counts."""

    count_only_class_dif: int = 0
    count_deleted_box: int = 0
    count_new_boxes: int = 0
    count_diff_boxes: int = 0


def percentage_diff(value1: float, value2: float) -> float:
    """
    Calculates the difference between values as a percentage.

    Parameters
    ----------
    value1:
        First value to calculate percentage difference.
    value2:
        Second value to calculate percentage difference.

    Returns
    -------
    float
        The difference between values as a percentage.

    """

    return abs((value1 - value2) / ((value1 + value2) / 2))


def parse_annotations_to_boxes(
    annotation_lines: list[str],
) -> list[BBox]:
    """
    Parse annotation strings to bboxes sorted by coordinates of centers.

    Parameters
    ----------
    annotation_lines: list[str]
        Lines from annotation file.

    Returns
    -------
    list[BBox]
        Parsed boxes, sorted by coordinates of canters.

    """

    boxes = [BBox(*[float(w) for w in annotation_line[:-2].split()]) for annotation_line in annotation_lines]
    boxes = sorted(boxes, key=lambda bbox: (bbox.x_center, bbox.y_center))

    return boxes


def is_box_unchanged(
    initial_box: BBox,
    final_box: BBox,
    box_change_low_threshold: float,
) -> bool:
    """
    Check whether box was changed enough to be counted as changed.

    Parameters
    ----------
    initial_box: BBox
        Box from initial labels.
    final_box: BBox
        Box from final labels.
    box_change_low_threshold: float
        If change is lower than this threshold, box counted as unchanged.

    Returns
    -------
    bool
        True, if box is unchanged.

    """

    return all(
        (
            percentage_diff(value1=initial_box.width, value2=final_box.width) < box_change_low_threshold,
            percentage_diff(value1=initial_box.height, value2=final_box.height) < box_change_low_threshold,
            percentage_diff(value1=initial_box.x_center, value2=final_box.x_center) < box_change_low_threshold,
            percentage_diff(value1=initial_box.y_center, value2=final_box.y_center) < box_change_low_threshold,
        ),
    )


def is_box_changed(
    initial_box: BBox,
    final_box: BBox,
    box_change_low_threshold: float,
    box_change_high_threshold: float,
) -> bool:
    """
    Check is all box changes between thresholds.

    Parameters
    ----------
    initial_box: BBox
        Box from initial labels.
    final_box: BBox
        Box from final labels.
    box_change_low_threshold: float
        If change is lower than this threshold, box counted as unchanged.
    box_change_high_threshold:
        If change is higher than this threshold, box counted as deleted.

    Returns
    -------
    bool
        True if box is changed.

    """
    box_changed = any(
        (
            box_change_low_threshold
            < percentage_diff(value1=initial_box.width, value2=final_box.width)
            < box_change_high_threshold,
            box_change_low_threshold
            < percentage_diff(value1=initial_box.height, value2=final_box.height)
            < box_change_high_threshold,
            box_change_low_threshold
            < abs(initial_box.y_center - final_box.y_center) / initial_box.height
            < box_change_high_threshold,
            box_change_low_threshold
            < abs(initial_box.x_center - final_box.x_center) / initial_box.width
            < box_change_high_threshold,
        ),
    )

    return box_changed


def is_deleted_box(
    initial_box: BBox,
    final_box: BBox,
    box_change_high_threshold: float,
) -> bool:
    """
    Check whether box was changed enough to be counted as deleted.

    Parameters
    ----------
    initial_box: BBox
        Box from initial labels.
    final_box: BBox
        Box from final labels.
    box_change_high_threshold:
        If change is higher than this threshold, box counted as deleted.

    Returns
    -------
    bool
        True if box is deleted.

    """

    box_deleted = any(
        (
            percentage_diff(value1=initial_box.width, value2=final_box.width) > box_change_high_threshold,
            percentage_diff(value1=initial_box.height, value2=final_box.height) > box_change_high_threshold,
            (abs(initial_box.y_center - final_box.y_center) / initial_box.height) > box_change_high_threshold,
            (abs(initial_box.y_center - final_box.y_center) / initial_box.height) > box_change_high_threshold,
        ),
    )

    return box_deleted


def count_salary(costs_params_cfg: CostsParamsConfig) -> tuple:
    """
    Calculates the amount earned for the changed/added boxes.

    Parameters
    ----------
    costs_params_cfg: CostsParamsConfig
        Config with thresholds and costs for new/changed/deleted boxes

    Returns
    -------
    tuple
        Tuple with data for salary table
    """

    salary = 0
    box_counts = BoxCounts()
    initial_img_files = sorted(list(costs_params_cfg.initial_labels_path.glob("*.jpg")))

    if not costs_params_cfg.have_preannotated or len(initial_img_files) == 0:
        final_labels_files = sorted(list(costs_params_cfg.final_labels_path.glob("*.txt")))
        
        if costs_params_cfg.frames_to == -1:
            final_labels_files = final_labels_files[costs_params_cfg.frames_from:]
        else:
            final_labels_files = final_labels_files[costs_params_cfg.frames_from : costs_params_cfg.frames_to]
        
        for file_num, final_labels_file in tqdm(enumerate(final_labels_files), desc="Analyze files..."):
            is_frame_increased = (
                costs_params_cfg.increased_cost_frame_from <= file_num <= costs_params_cfg.increased_cost_frame_to
            )

            with open(final_labels_file, "r", encoding="utf-8") as file:
                final_boxes_str = file.readlines()

            final_boxes = parse_annotations_to_boxes(final_boxes_str)
            
            salary += (
                len(final_boxes) * costs_params_cfg.box_costs_cfg.cost_new_box_increased
                if is_frame_increased
                else len(final_boxes) * costs_params_cfg.box_costs_cfg.cost_new_box
            )
            box_counts.count_new_boxes += len(final_boxes)
    else:
        initial_labels_files = sorted(list(costs_params_cfg.initial_labels_path.glob("*.txt")))

        if costs_params_cfg.frames_to == -1:
            initial_labels_files = initial_labels_files[costs_params_cfg.frames_from:]
        else:
            initial_labels_files = initial_labels_files[costs_params_cfg.frames_from : costs_params_cfg.frames_to]
        
        for file_num, initial_labels_file in tqdm(enumerate(initial_labels_files), desc="Analyze files..."):
            is_frame_increased = (
                costs_params_cfg.increased_cost_frame_from <= file_num <= costs_params_cfg.increased_cost_frame_to
            )

            with open(initial_labels_file, "r", encoding="utf-8") as file:
                initial_boxes_str = file.readlines()

            final_labels_file = costs_params_cfg.final_labels_path / str(initial_labels_file).rsplit("/", maxsplit=1)[-1]
            if not final_labels_file.exists():
                continue
            with open(final_labels_file, "r", encoding="utf-8") as file:
                final_boxes_str = file.readlines()

            initial_boxes = parse_annotations_to_boxes(initial_boxes_str)
            final_boxes = parse_annotations_to_boxes(final_boxes_str)

            for initial_box in initial_boxes:
                if len(final_boxes) == 0:
                    salary += (
                        costs_params_cfg.box_costs_cfg.cost_diff_box_increased * len(initial_boxes)
                        if is_frame_increased
                        else costs_params_cfg.box_costs_cfg.cost_diff_box * len(initial_boxes)
                    )

                    box_counts.count_deleted_box += len(initial_boxes)
                    break

                for final_box in final_boxes:
                    if is_box_unchanged(
                        initial_box=initial_box,
                        final_box=final_box,
                        box_change_low_threshold=costs_params_cfg.box_change_low_threshold,
                    ):
                        if initial_box.obj_class != final_box.obj_class:

                            salary += (
                                costs_params_cfg.box_costs_cfg.cost_diff_box_increased
                                if is_frame_increased
                                else costs_params_cfg.box_costs_cfg.cost_diff_box
                            )
                            box_counts.count_only_class_dif += 1

                        final_boxes.remove(final_box)
                        break

                    if is_box_changed(
                        initial_box=initial_box,
                        final_box=final_box,
                        box_change_low_threshold=costs_params_cfg.box_change_low_threshold,
                        box_change_high_threshold=costs_params_cfg.box_change_high_threshold,
                    ):
                        salary += (
                            costs_params_cfg.box_costs_cfg.cost_diff_box_increased
                            if is_frame_increased
                            else costs_params_cfg.box_costs_cfg.cost_diff_box
                        )
                        box_counts.count_diff_boxes += 1
                        final_boxes.remove(final_box)
                        break

                    if is_deleted_box(
                        initial_box=initial_box,
                        final_box=final_box,
                        box_change_high_threshold=costs_params_cfg.box_change_high_threshold,
                    ):
                        salary += (
                            costs_params_cfg.box_costs_cfg.cost_diff_box_increased
                            if is_frame_increased
                            else costs_params_cfg.box_costs_cfg.cost_diff_box
                        )
                        box_counts.count_deleted_box += 1
                        break

            salary += (
                len(final_boxes) * costs_params_cfg.box_costs_cfg.cost_new_box_increased
                if is_frame_increased
                else len(final_boxes) * costs_params_cfg.box_costs_cfg.cost_new_box
            )
            box_counts.count_new_boxes += len(final_boxes)

    print("salary: ", salary)
    print("count new boxes: ", box_counts.count_new_boxes)
    print("count deleted box: ", box_counts.count_deleted_box)
    print("count only class dif: ", box_counts.count_only_class_dif)
    print("count changed boxes: ", box_counts.count_diff_boxes)

    return (
        salary, box_counts.count_new_boxes, 
        box_counts.count_deleted_box, 
        box_counts.count_only_class_dif, 
        box_counts.count_diff_boxes
    )


def main(args_path: Path | str):
    """Main function."""

    if args_path:
        with open(args_path, "r", encoding="utf-8") as yaml_file:
            args: dict = yaml.safe_load(yaml_file)
    else:
        raise ValueError("args_path is empty or invalid")

    if "increased_cost_frame_from" in args.keys() and "increased_cost_frame_to" in args.keys():
        increased_cost_frame_from = args["increased_cost_frame_from"]
        increased_cost_frame_to = args["increased_cost_frame_to"]
    else:
        increased_cost_frame_from = -1
        increased_cost_frame_to = -1

    box_costs_cfg = BoxCostsConfig(
        cost_diff_box=args["cost_diff_box"],
        cost_diff_box_increased=args["cost_diff_box_increased"],
        cost_new_box=args["cost_new_box"],
        cost_new_box_increased=args["cost_new_box_increased"],
    )

    costs_params_cfg = CostsParamsConfig(
        initial_labels_path=Path(args["initial_labels_dir"]),
        final_labels_path=Path(args["final_labels_dir"]),
        box_costs_cfg=box_costs_cfg,
        box_change_low_threshold=args["box_change_low_threshold"],
        box_change_high_threshold=args["box_change_high_threshold"],
        increased_cost_frame_from=increased_cost_frame_from,
        increased_cost_frame_to=increased_cost_frame_to,
    )

    count_salary(costs_params_cfg=costs_params_cfg)


if __name__ == "__main__":
    CLI(main, as_positional=False)
