from pathlib import Path

import pandas as pd

from src.preprocessing.teams.preprocessor import Preprocessor
from src.scrapping.scrape_teams.get_urls import TeamUrlsScrapper
from src.scrapping.scrape_teams.scrapper import TeamsScrapper
from src.utils.team_aliases import extract_team_slug

TEAMS_BASE_URL = "https://www.salaooval.com.br/times/"

RAW_TEAMS_DIR = Path("data/raw/teams")
RAW_TEAMS_LATEST_PATH = RAW_TEAMS_DIR / "teams_latest.csv"
SEED_TEAMS_PATH = Path("backend/seed_data/teams.csv")


def scrape_teams(output_path: Path = RAW_TEAMS_LATEST_PATH) -> Path:
    """Scrapes the full team roster and overwrites one fixed file, rather than
    writing a new timestamped file every run. Unlike games, there's no incremental
    filter here - TeamUrlsScrapper's REST-based discovery returns every published
    team every time, so each run is already a full, self-sufficient snapshot. A
    "never overwrite" convention (as games uses, for genuinely incremental deltas)
    would mean committing a near-complete duplicate of the ~430-team roster on every
    run for no benefit - reconcile_teams_csv only ever needs the latest snapshot,
    never a merge of past ones."""
    RAW_TEAMS_DIR.mkdir(parents=True, exist_ok=True)

    urls_scrapper = TeamUrlsScrapper(base_url=TEAMS_BASE_URL)
    urls = urls_scrapper.get_urls()

    teams_scrapper = TeamsScrapper(urls, save_path=str(output_path))
    teams_scrapper.scrape_teams(init=0, end=len(urls), verbose=True)

    return output_path


def reconcile_teams_csv(
    raw_teams_path: Path,
    existing_seed_path: Path = SEED_TEAMS_PATH,
    output_path: Path = SEED_TEAMS_PATH,
) -> Path:
    """Applies team-name aliases and Sede-derived Estado/Regiao (via the existing
    Preprocessor) to one fresh full team scrape, then carries Estado/Regiao forward
    from the already-committed seed file by team-page URL slug wherever the fresh
    scrape couldn't derive them - most bio pages don't have a parseable Sede, so this
    is the common case, not the exception. Replicates the 2026-08-26 manual
    reconciliation: matching by slug (not name) survives a display-name change.
    Also drops any row with a genuinely blank name, and on an alias-induced name
    collision (e.g. two site pages later aliased to the same canonical name) keeps
    whichever row already has a populated Estado."""
    preprocessor = Preprocessor()
    preprocessor.original_teams_df = pd.read_csv(raw_teams_path)
    teams_df = preprocessor.preprocess_teams_df()

    teams_df = teams_df[teams_df["Nome"].notna() & (teams_df["Nome"].str.strip() != "")]

    if existing_seed_path.exists():
        existing_df = pd.read_csv(existing_seed_path)
        slug_lookup = {
            slug: (row["Estado"], row["Regiao"])
            for _, row in existing_df.iterrows()
            if (slug := extract_team_slug(row["URL"])) is not None
        }

        def _carry_forward(row: pd.Series) -> pd.Series:
            if pd.isna(row["Estado"]):
                old = slug_lookup.get(extract_team_slug(row["URL"]))
                if old is not None:
                    row["Estado"], row["Regiao"] = old
            return row

        teams_df = teams_df.apply(_carry_forward, axis=1)

    teams_df = (
        teams_df.sort_values(by="Estado", key=lambda s: s.isna())
        .drop_duplicates(subset=["Nome"], keep="first")
        .sort_values(by="Nome")
        .reset_index(drop=True)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    teams_df.to_csv(output_path, index=False)

    return output_path
