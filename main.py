import os
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint

from PIL import Image

SUBFOLDER_NAMES = [
    "master",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
]

OUTPUT_FOLDER_NAME = "output"


def last_number(filename: str) -> int:
    return int(filename.split(".")[0].split("_")[-1])


def get_date_from_image(path: Path) -> datetime:
    info = Image.open(path).getexif().get_ifd(0x8769)
    datestring, timestring = info[0x9003].split(" ")
    datelist = [int(i) for i in datestring.split(":")]
    timelist = [int(i) for i in timestring.split(":")]
    return datetime(
        year=datelist[0], month=datelist[1], day=datelist[2],
        hour=timelist[0], minute=timelist[1], second=timelist[2]
    )


def generate_gif(image_paths: list[Path], output_path: Path):
    frames = [Image.open(frame) for frame in image_paths]
    frames = frames + frames[::-1]
    frames[0].save(
        fp=output_path, save_all=True, append_images=frames, duration=75, loop=0
    )


def get_average_light_value(path: Path) -> int:
    image = Image.open(path)
    image.thumbnail((1, 1))
    return sum(image.getpixel((0, 0)))


def get_first_batch_times(root_path: Path) -> list[datetime]:
    source_folders = [root_path / folder_name for folder_name in SUBFOLDER_NAMES]
    times: list[datetime] = []
    for folder in source_folders:
        filenames = sorted(os.listdir(folder), key=last_number)
        times.append(get_date_from_image(folder / filenames[0]))
    return times


def batch_gifs(input_dict: dict[int, dict[datetime, Path]], first_batch_times: list[datetime]) -> list[list[Path]]:
    master_dict = input_dict.pop(0)
    batches: list[list[Path]] = []
    for master_capture_time in master_dict:
        current_batch = []
        for i in input_dict:
            batch_slice = []
            for capture_time in input_dict[i]:
                time_diff = abs(
                    (master_capture_time - first_batch_times[0]) - (capture_time - first_batch_times[i])
                )
                if time_diff <= timedelta(seconds=0):
                    batch_slice.append(input_dict[i][capture_time])
                    break
            if not batch_slice:
                for capture_time in input_dict[i]:
                    # print("Not found 0 timedelta")
                    time_diff = abs(
                        (master_capture_time - first_batch_times[0]) - (capture_time - first_batch_times[i])
                    )
                    if time_diff <= timedelta(seconds=1):
                        batch_slice.append(input_dict[i][capture_time])
                        if len(batch_slice) > 1:
                            print(f"More than one image found for {master_dict[master_capture_time]}, "
                                  f"Folder: {i + 1}, image: {input_dict[i][capture_time]}")
                            current_batch.append(batch_slice[0])
            else:
                current_batch += batch_slice
        print(f"{len(batches)}: {len(current_batch)}")
        batches.append(current_batch)
    return batches


def parse_folders(root_path: Path) -> dict[int, dict[datetime, Path]]:
    # Master should be first one
    source_folders = [root_path / folder_name for folder_name in SUBFOLDER_NAMES]
    output = {}
    for i in range(len(source_folders)):
        filenames = sorted(os.listdir(source_folders[i]), key=last_number)
        for filename in filenames:
            file_path = source_folders[i] / filename
            light = get_average_light_value(file_path)
            if light < 30:
                print(f"File {str(file_path)} underexposed!")
                continue
            capture_time = get_date_from_image(file_path)
            if i not in output:
                output[i] = {}
            output[i][capture_time] = file_path
    return output


def main(root_path):
    output_folder = root_path / OUTPUT_FOLDER_NAME
    output_folder.mkdir(exist_ok=True)

    start_time = time.time()
    print("Analyzing input images...")
    first_batch_times = get_first_batch_times(root_path)
    sorted_paths = parse_folders(root_path)

    print("Folder sizes:")
    for i in sorted_paths:
        print(f"\t{i}: {len(sorted_paths[i])}")

    print("Creating batches...")
    batches = batch_gifs(sorted_paths, first_batch_times)
    number_of_batches = len(batches)

    if 1:
        for i in range(len(batches)):
            output_path = output_folder / (str(i) + ".gif")
            print(f"[{i} / {number_of_batches}] {output_path}")
            generate_gif(batches[i], output_path)
            if i == -1:
                break

    elapsed_seconds = time.time() - start_time

    print(
        f"Done! That took {round(elapsed_seconds, 2)} seconds, "
        f"around {round(elapsed_seconds / number_of_batches, 2)} seconds per gif."
    )


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
    main(root_path)
