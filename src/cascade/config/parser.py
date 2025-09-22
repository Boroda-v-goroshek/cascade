# function for parsing input data
import argparse


def get_parser() -> argparse.ArgumentParser:
    '''
    Returns
    -------
    argparse.ArgumentParser
        parser with comand line arguments
    '''
    parser = argparse.ArgumentParser(description="Loading configuration")
    parser.add_argument(
        "--config-path",
        "-cfg",
        type=str,
        help="Path to yml config",
        required=True,
    )

    return parser