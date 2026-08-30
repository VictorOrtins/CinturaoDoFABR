import colorsys
import requests

from datetime import datetime

import numpy as np

from sklearn.cluster import KMeans
from PIL import Image


def get_dominant_color(
    image_url: str,
    k: int = 3,
    exclude_white: bool = True,
    exclude_black: bool = True,
    tolerance: int = 30,
):
    def _load_image(image_url: str) -> np.ndarray:

        img = Image.open(requests.get(image_url, stream=True, timeout=30).raw).convert('RGBA')
        img_array = np.array(img)

        return img_array

    def _get_mask(img_array: np.ndarray, exclude_black_now: bool) -> np.ndarray:
        mask = (img_array[:, :, 3] > 0)  # Canal alfa > 0 (não transparente)
        if exclude_white:
            # Define o que é considerado "branco" (com tolerância)
            white_mask = np.all(
                np.abs(img_array[:, :, :3] - [255, 255, 255]) < tolerance,
                axis=2
            )
            mask = mask & ~white_mask
        if exclude_black_now:
            # Logos commonly outline/stroke shapes in black - without this, that
            # outline (not the actual brand color) usually wins on raw pixel count.
            black_mask = np.all(
                np.abs(img_array[:, :, :3].astype(int) - [0, 0, 0]) < tolerance,
                axis=2
            )
            mask = mask & ~black_mask

        return mask

    def _saturation(rgb: np.ndarray) -> float:
        r, g, b = (rgb / 255.0).clip(0, 1)
        _, s, _ = colorsys.rgb_to_hsv(r, g, b)
        return s

    def _k_means_dominant_color(pixels: np.ndarray, k: int):
        # Fixed seed: without it, KMeans's random centroid init makes the
        # winning cluster's averaged RGB drift by ~1 per channel between
        # re-scrapes of the same unchanged logo image, manufacturing spurious
        # teams.csv diffs on every scheduled scrape (found via a real Phase 5
        # end-to-end run, 2026-08-30 - 16 teams' colors jittered with zero
        # actual logo changes).
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=0)
        kmeans.fit(pixels)
        counts = np.bincount(kmeans.labels_, minlength=k)
        # Weight by saturation so a small but clearly-branded-colored cluster beats
        # a larger muddy/gray one; the small constant keeps count as a tiebreaker
        # when every cluster is roughly grayscale (saturation ~0 for all of them).
        scores = [
            counts[i] * (_saturation(kmeans.cluster_centers_[i]) + 0.05)
            for i in range(k)
        ]
        dominant_color = kmeans.cluster_centers_[np.argmax(scores)]

        return dominant_color

    img_array = _load_image(image_url)

    mask = _get_mask(img_array, exclude_black_now=exclude_black)
    pixels = img_array[mask][:, :3]  # Pega apenas RGB

    dominant_color = _k_means_dominant_color(pixels, k) if len(pixels) > 0 else None

    # A genuinely monochrome-black-branded logo (e.g. an "all blacks" theme) has
    # nothing left but low-saturation anti-aliasing pixels once black is excluded -
    # that yields a washed-out gray, not a real brand color. Detect that by the
    # *result*'s saturation (not pixel count, which anti-aliasing gradients can pad
    # without adding real color signal) and fall back to keeping black.
    if exclude_black and (dominant_color is None or _saturation(dominant_color) < 0.15):
        mask = _get_mask(img_array, exclude_black_now=False)
        pixels = img_array[mask][:, :3]
        dominant_color = _k_means_dominant_color(pixels, k) if len(pixels) > 0 else None

    # Se não houver pixels válidos, retorna None
    if dominant_color is None:
        return None

    hex_color = "#{:02x}{:02x}{:02x}".format(*dominant_color.astype(int))
    return hex_color



def is_datetime(value):
    format_date = "%Y-%m-%d %H:%M:%S"

    try:
        datetime.strptime(value, format_date)
        return True
    except ValueError:
        return False