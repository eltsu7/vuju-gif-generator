import os
import shutil
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint

from PIL import Image

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
    if len(image_paths) == 0:
        print("No images!")
        return
    frames[0].save(
        fp=output_path, save_all=True, append_images=frames, duration=75, loop=0, optimize=True
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


def find_closest_image(folder: dict[datetime, Path], master_time: timedelta, master_file: Path, folder_time_offset: datetime) -> list[Path]:
    paths: list[Path] = []
    for delta in [0, 1, 2, 3]:
        for capture_time in folder:
            time_diff = abs(
                master_time - (capture_time - folder_time_offset)
            )
            if time_diff <= timedelta(seconds=delta):
                paths.append(folder[capture_time])
        if len(paths) > 0:
            break
    if len(paths) == 1:
        return paths
    elif len(paths) == 0:
        print("0 frames found for", str(master_file))
    else:
        print(f"More than 1 frames found for {str(master_file)}: {paths}")
    return paths


def batch_gifs(input_dict: dict[int, dict[datetime, Path]], first_batch_times: list[datetime]) -> list[list[Path]]:
    master_dict = input_dict.pop(0)
    batches: list[list[Path]] = []
    for master_capture_time in master_dict:
        current_batch = []
        for i in input_dict:
            batch_slice = find_closest_image(
                input_dict[i],
                master_capture_time - first_batch_times[0],
                master_dict[master_capture_time],
                first_batch_times[i],
            )
            current_batch += batch_slice
        print(f"{len(batches)}: {len(current_batch)}")
        batches.append(current_batch)
    input_dict[0] = master_dict
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
    batch_folder: Path = root_path / "batches"

    start_time = time.time()
    if not batch_folder.exists():
        batch_folder.mkdir(exist_ok=True)
        print("Analyzing input images...")
        first_batch_times = get_first_batch_times(root_path)
        sorted_paths = parse_folders(root_path)

        print("Folder sizes:")
        for i in sorted_paths:
            print(f"\t{i}: {len(sorted_paths[i])}")

        print("Creating batches...")
        batches = batch_gifs(sorted_paths, first_batch_times)
        number_of_batches = len(batches)

        for i in range(len(batches)):
            (batch_folder / str(i)).mkdir(exist_ok=True, parents=True)
            master = list(sorted_paths[0].values())[i]
            shutil.copy(master, batch_folder / str(i))

            for cam_number in range(len(batches[i])):  # TODO tää ei oo cam number
                file = batches[i][cam_number]
                shutil.copy(file, batch_folder / str(i) / (str(cam_number) + "_" + os.path.basename(file)))

        print(os.listdir(batch_folder))

    for batch in os.listdir(batch_folder):
        if not (batch_folder / batch).is_dir():
            continue
        batch_files = os.listdir(batch_folder / batch)
        for i in range(len(batch_files)):
            if batch_files[i].lower().startswith("master"):
                batch_files.pop(i)
        output_path = output_folder / (batch + ".gif")
        print(f"Creating {output_path} with {len(batch_files)} images..")
        generate_gif([batch_folder / batch / filename for filename in batch_files], output_path)

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
