import requests

from datetime import datetime
from io import BytesIO

import numpy as np

from sklearn.cluster import KMeans
from PIL import Image





def get_dominant_color(image_url: str, k: int = 3, exclude_white: bool = True, tolerance: int = 30):
    def _load_image(image_url: str) -> np.ndarray:

        img = Image.open(requests.get(image_url, stream=True).raw).convert('RGBA')
        img_array = np.array(img)

        return img_array
    
    def _get_mask(img_array: np.ndarray) -> np.ndarray:
        mask = (img_array[:, :, 3] > 0)  # Canal alfa > 0 (não transparente)
        if exclude_white:
            # Define o que é considerado "branco" (com tolerância)
            white_mask = np.all(
                np.abs(img_array[:, :, :3] - [255, 255, 255]) < tolerance,
                axis=2
            )
            mask = mask & ~white_mask

        return mask
    
    def _k_means_dominant_color(pixels: np.ndarray, k: int):
        kmeans = KMeans(n_clusters=k, n_init=10)
        kmeans.fit(pixels)
        dominant_color = kmeans.cluster_centers_[np.argmax(np.bincount(kmeans.labels_))]

        return dominant_color
    
    img_array = _load_image(image_url)

    mask = _get_mask(img_array)

    pixels = img_array[mask][:, :3]  # Pega apenas RGB

    # Se não houver pixels válidos, retorna None
    if len(pixels) == 0:
        return None

    dominant_color = _k_means_dominant_color(pixels, k)

    hex_color = "#{:02x}{:02x}{:02x}".format(*dominant_color.astype(int))
    return hex_color



def is_datetime(value):
    format_date = "%Y-%m-%d %H:%M:%S"

    try:
        datetime.strptime(value, format_date)
        return True
    except ValueError:
        return False