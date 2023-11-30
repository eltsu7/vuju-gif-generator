import os

import argparse
from pathlib import Path

from gifs import generate_gifs


SUBFOLDER_NAMES = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
]

OUTPUT_FOLDER_NAME = "output"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()

    root_path: Path = args.folder
    if not os.path.exists(root_path):
        raise NameError("Invalid path")

    for name in SUBFOLDER_NAMES:
        if not os.path.exists(root_path / name):
            raise NameError("Can't find correct subfolders")

    source_folders = [root_path / folder_name for folder_name in SUBFOLDER_NAMES]

    output_folder = root_path / OUTPUT_FOLDER_NAME
    os.makedirs(output_folder, exist_ok=True)

    generate_gifs(source_folders, output_folder)
