"""Recomputes each team's `Cor Primária` from its already-known logo URL, without
re-scraping the site.

Background: `get_dominant_color` (src/utils/utils.py) used to only exclude
near-white pixels before picking the k-means cluster with the most pixels as "the"
color - logo outlines/strokes are commonly black, so that cluster often won on raw
pixel count over the actual brand color. Fixed to also exclude near-black pixels and
weight cluster choice by saturation, not just size. This script re-applies the fixed
algorithm against every team's stored `URL da Imagem` (present in both
backend/seed_data/teams.csv and data/raw/teams/teams_bootstrap.csv) - no Selenium, no
new scraping capability, just re-downloading each logo image.

Usage:
    python -m src.pipeline.recompute_team_colors backend/seed_data/teams.csv
    python -m src.pipeline.recompute_team_colors data/raw/teams/teams_bootstrap.csv --dry-run
"""

import argparse
from pathlib import Path

import pandas as pd

from src.utils.utils import get_dominant_color


def recompute_colors(csv_path: Path, dry_run: bool = False) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    old_colors = df["Cor Primária"].copy()
    new_colors = []

    for _, row in df.iterrows():
        image_url = row["URL da Imagem"]
        old_color = row["Cor Primária"]

        if pd.isna(image_url):
            new_colors.append(old_color)
            continue

        try:
            color = get_dominant_color(image_url)
        except Exception as e:
            print(f"[warn] {row['Nome']}: failed to recompute ({e}) - keeping old color")
            color = None

        new_colors.append(color if color is not None else old_color)

    df["Cor Primária"] = new_colors

    changed = df[old_colors != df["Cor Primária"]][["Nome", "URL da Imagem"]].copy()
    changed["De"] = old_colors[old_colors != df["Cor Primária"]]
    changed["Para"] = df.loc[changed.index, "Cor Primária"]
    print(f"{len(changed)}/{len(df)} colors changed")
    print(changed.to_string(index=False))

    if not dry_run:
        df.to_csv(csv_path, index=False)

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="Path to a teams CSV with 'URL da Imagem'/'Cor Primária' columns")
    parser.add_argument("--dry-run", action="store_true", help="Print the diff without writing the file")
    args = parser.parse_args()

    recompute_colors(args.csv_path, dry_run=args.dry_run)
