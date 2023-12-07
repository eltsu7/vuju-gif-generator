import os
import shutil
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint

from PIL import Image, GifImagePlugin

SUBFOLDER_NAMES = [
    "master",
    "Cam1",
    "Cam2",
    "Cam3",
    "Cam4",
    "Cam5",
    "Cam6",
    "Cam7",
]

OUTPUT_FOLDER_NAME = "output_2"
BATCH_FOLDER_NAME = "batches"


def last_number(filename: str) -> int:
    return int(filename.split(".")[0].split("_")[-1])


def get_date_from_image(path: Path) -> datetime:
    info = Image.open(path).getexif().get_ifd(0x8769)
    datestring, timestring = info[0x9003].split(" ")
    datelist = [int(i) for i in datestring.split(":")]
    timelist = [int(i) for i in timestring.split(":")]
    return datetime(
        year=datelist[0],
        month=datelist[1],
        day=datelist[2],
        hour=timelist[0],
        minute=timelist[1],
        second=timelist[2],
    )


def generate_gif(image_paths: list[Path], output_path: Path):
    frames = [Image.open(frame) for frame in image_paths]
    frames = frames + frames[::-1]
    if len(image_paths) == 0:
        print("No images!")
        return
    frames[0].save(
        fp=output_path,
        save_all=True,
        append_images=frames[1:],
        duration=75,
        loop=0,
        optimize=True,
    )


def get_average_light_value(path: Path) -> int:
    image = Image.open(path)
    image.thumbnail((1, 1))
    return sum(image.getpixel((0, 0)))


def find_with_timedelta(
    master_folder: Path, master_index: int, sub_folder: Path, time_delta: timedelta
):
    master_file = master_folder / os.listdir(master_folder)[master_index]
    time_offset = get_date_from_image(
        master_folder / os.listdir(master_folder)[0]
    ) - get_date_from_image(sub_folder / os.listdir(sub_folder)[0])

    if os.path.basename(sub_folder) == "Cam1":
        time_offset -= timedelta(seconds=1)

    master_time = get_date_from_image(master_file) - time_offset

    paths = []

    for filename in os.listdir(sub_folder):
        if abs(master_time - get_date_from_image(sub_folder / filename)) <= time_delta:
            paths.append(sub_folder / filename)

    return paths


def new_batch_files_to_folders(root_path):
    output_folder = root_path / OUTPUT_FOLDER_NAME
    output_folder.mkdir(exist_ok=True)
    batch_folder: Path = root_path / BATCH_FOLDER_NAME
    master_folder = root_path / "master"

    for i in range(len(os.listdir(master_folder))):
        if (batch_folder / str(i)).exists():
            continue

        current_batch_folder = batch_folder / str(i)
        print(f"Master: {os.listdir(master_folder)[i]}")
        paths: list[Path] = []
        for sub in SUBFOLDER_NAMES[1:]:
            paths += find_with_timedelta(
                master_folder, i, root_path / sub, timedelta(seconds=2)
            )

        current_batch_folder.mkdir(parents=True)
        shutil.copy(
            master_folder / (os.listdir(master_folder)[i]), current_batch_folder
        )
        for path in paths:
            print("\t" + str(path))
            new_file_name = (
                os.path.basename(os.path.split(path)[0]) + "_" + os.path.split(path)[1]
            )
            shutil.copy(path, current_batch_folder / new_file_name)


def new_batches_to_gifs(root_path):
    output_folder = root_path / OUTPUT_FOLDER_NAME
    output_folder.mkdir(exist_ok=True)
    batch_folder: Path = root_path / BATCH_FOLDER_NAME

    for batch in os.listdir(batch_folder):
        if not (batch_folder / batch).is_dir():
            continue
        batch_files = os.listdir(batch_folder / batch)
        for i in range(len(batch_files)):
            if batch_files[i].lower().startswith("master"):
                batch_files.pop(i)
        output_path = output_folder / (batch + ".gif")
        print(f"Creating {output_path} with {len(batch_files)} images..")
        generate_gif(
            [batch_folder / batch / filename for filename in batch_files], output_path
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()

    root_path_arg: Path = args.folder
    if not os.path.exists(root_path_arg):
        raise NameError("Invalid path")
    for name in SUBFOLDER_NAMES:
        if not os.path.exists(root_path_arg / name):
            raise NameError("Can't find correct subfolders")
    # new_batch_files_to_folders(root_path_arg)
    new_batches_to_gifs(root_path_arg)
