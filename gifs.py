from pathlib import Path
import os

import cv2
from PIL import Image


def generate_gifs(source_folders: list[Path], output_folder: Path):
    image_paths: dict[str, list[Path]] = {}

    for path in source_folders:
        files = [path / filename for filename in os.listdir(path)]
        files.sort(key=lambda x: os.path.getmtime(x))
        image_paths[os.path.split(path)[-1]] = files

    smallest_length = min([len(image_paths[f]) for f in image_paths])

    print(smallest_length)

    for i in range(1):
        gif_images = []
        for folder in image_paths:
            gif_images.append(Image.open(image_paths[folder][i]))
            # gif_images.append(image_paths[folder][i])

        output_file_path = output_folder / (str(i) + ".gif")

        img = Image.Image()

        img.save(fp=output_file_path, append_images=gif_images)
