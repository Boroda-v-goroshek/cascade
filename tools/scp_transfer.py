from typing import cast

from omegaconf import DictConfig

from src.cascade.config.parser import get_parser
from src.cascade.config.config_loader import load_config
from src.cascade.tools.data_transfer import DataTransfer


def transfer(opts: DictConfig):
    transfer = DataTransfer(opts.server_conf)
    transfer.transfer_data(opts.local_path, opts.remote_path, opts.server_name, opts.mode)

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    opts = load_config(args.config_path)
    transfer(opts)

