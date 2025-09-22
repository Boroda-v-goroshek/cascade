import argparse
from pathlib import Path
from typing import cast

import yaml
from omegaconf import DictConfig
from omegaconf import OmegaConf


def load_config(cfg_path: str | Path, args: dict | None = None) -> DictConfig:
    """Function for load config file using OmegaConf.

    Parameters
    ----------
    cfg_path: str | Path
        path to config file
    args: dict | None
        args from console for add in config file

    Returns
    -------
    DictConfig
        Full config with console arguments

    """
    with open(cfg_path) as ymfile:
        cfg = yaml.load(ymfile, Loader=yaml.FullLoader)

    cfg: DictConfig = OmegaConf.create(cfg)

    if args is not None:
        args_dict = vars(args) if isinstance(args, argparse.Namespace) else args
        cfg = cast(DictConfig, OmegaConf.merge(cfg, args_dict))

    return cfg
