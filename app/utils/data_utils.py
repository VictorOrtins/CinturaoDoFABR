import requests

import pandas as pd

from PIL import Image


def read_csv_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def read_image_from_url(image_url: str) -> Image:
    return Image.open(requests.get(image_url, stream=True).raw).convert('RGBA')

def resize_img(image: Image, new_height: int) -> Image:
    height, width = int(image.size[0]), int(image.size[1])
    new_width = int(new_height * width/height)
    return image.resize((new_width, new_height), Image.LANCZOS)

    
