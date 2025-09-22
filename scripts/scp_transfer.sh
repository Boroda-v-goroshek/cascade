export PYTHONPATH="${PYTHONPATH}:$(pwd)"

python tools/scp_transfer.py \
-cfg configs/scp_transfer.yml