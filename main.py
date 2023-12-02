import os
import time
import argparse
from pathlib import Path

from PIL import Image

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


def last_number(filename: str) -> int:
    return int(filename.split(".")[0].split("-")[-1])


def generate(image_paths: list[Path], output_path: Path):
    frames = [Image.open(frame) for frame in image_paths]
    frames = frames + frames[::-1]
    frames[0].save(
        fp=output_path, save_all=True, append_images=frames, duration=75, loop=0
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

    source_folders = [root_path / folder_name for folder_name in SUBFOLDER_NAMES]

    source_images = []
    for folder in source_folders:
        filenames = sorted(os.listdir(folder), key=last_number)
        source_images.append([folder / filename for filename in filenames])

    gif_batches = []

    try:
        i = 0
        while True:
            gif_batches.append([images[i] for images in source_images])
            i += 1
    except IndexError:
        pass

    output_folder = root_path / OUTPUT_FOLDER_NAME
    os.makedirs(output_folder, exist_ok=True)

    start_time = time.time()
    number_of_gifs = len(gif_batches)
    print("Starting to generate gifs..")

    for i, batch in enumerate(gif_batches):
        output_path = output_folder / (str(i) + ".gif")
        print(f"[{i} / {number_of_gifs}] {output_path}")
        generate(batch, output_path)
        break

    elapsed_seconds = time.time() - start_time

    print(
        f"Done! That took {round(elapsed_seconds, 2)} seconds, "
        f"around {round(elapsed_seconds / number_of_gifs, 2)} seconds per gif."
    )
