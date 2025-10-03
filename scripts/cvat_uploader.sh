export PYTHONPATH="${PYTHONPATH}:$(pwd)"

python tools/upload2cvat.py --args_path configs/upload2cvat.yml