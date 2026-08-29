from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.cinturao_algorithm.cinturao import Cinturao
from src.preprocessing.games.preprocessor import Preprocessor
from src.scrapping.scrape_games.get_urls import TournamentUrlsScrapper, filter_urls_by_year
from src.scrapping.scrape_games.scrapper import GamesScrapper

TOURNAMENTS_BASE_URL = "http://www.salaooval.com.br/campeonatos/"

RAW_GAMES_DIR = Path("data/raw/games")
RAW_GAMES_ACCUMULATED_PATH = RAW_GAMES_DIR / "games_accumulated.csv"
PROCESSED_DIR = Path("data/processed")
UNRESOLVED_TEAMS_PATH = Path("data/raw/unresolved_teams.txt")
SEED_GAMES_PATH = Path("backend/seed_data/games.csv")
SEED_TEAMS_PATH = Path("backend/seed_data/teams.csv")

GAMES_DEDUPE_KEY = ["Data", "Mandante", "Hor/Res", "Visitante", "Torneio"]


def scrape_recent_games(since_year: int) -> Path:
    """Scrapes tournaments from since_year onward and writes them to a new,
    timestamped file under data/raw/games/ (never overwrites a prior run). Used by
    update_games.py's manual/occasional CLI workflow. NOT used by the recurring
    Airflow DAG - see scrape_recent_games_accumulated for why."""
    RAW_GAMES_DIR.mkdir(parents=True, exist_ok=True)

    urls_scrapper = TournamentUrlsScrapper(base_url=TOURNAMENTS_BASE_URL, category="masculino")
    urls = filter_urls_by_year(urls_scrapper.get_urls(), since_year)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = RAW_GAMES_DIR / f"games_{timestamp}.csv"

    games_scrapper = GamesScrapper(urls, save_path=str(output_path))
    games_scrapper.scrape_tournaments(init=0, end=len(urls), verbose=True)

    return output_path


def scrape_recent_games_accumulated(since_year: int, accumulated_path: Path = RAW_GAMES_ACCUMULATED_PATH) -> Path:
    """Like scrape_recent_games, but merges the fresh scrape into one growing,
    deduped file instead of writing a new timestamped file every run.

    since_year covers a rolling ~1-2 year window, not "since the last run" - a new
    timestamped file every run means every run commits a mostly-duplicate copy of
    that same window forever (real, compounding repo growth with no correctness
    benefit, since merge_and_preprocess already dedupes everything downstream
    anyway). This keeps raw storage proportional to genuinely new games found, not
    to run frequency. This is what the recurring Airflow DAG uses; the older
    per-run-timestamped bootstrap/delta files already committed under
    data/raw/games/ are untouched and still get picked up by
    merge_and_preprocess's directory scan, so no historical data is lost by this
    file existing alongside them."""
    urls_scrapper = TournamentUrlsScrapper(base_url=TOURNAMENTS_BASE_URL, category="masculino")
    urls = filter_urls_by_year(urls_scrapper.get_urls(), since_year)

    games_scrapper = GamesScrapper(urls, save_path=None)
    fresh_df = games_scrapper.scrape_tournaments(init=0, end=len(urls), verbose=True)

    combined_df = merge_into_accumulated_games(accumulated_path, fresh_df)

    accumulated_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(accumulated_path, index=False)

    return accumulated_path


def merge_into_accumulated_games(accumulated_path: Path, fresh_df: pd.DataFrame) -> pd.DataFrame:
    """Pure merge/dedupe step split out of scrape_recent_games_accumulated so it's
    testable without a live scrape: union whatever's already at accumulated_path (if
    anything) with a fresh scrape, deduped by the same key merge_and_preprocess uses
    downstream."""
    if accumulated_path.exists():
        combined_df = pd.concat([pd.read_csv(accumulated_path), fresh_df], ignore_index=True)
    else:
        combined_df = fresh_df

    return combined_df.drop_duplicates(subset=GAMES_DEDUPE_KEY)


def merge_and_preprocess(raw_dir: Path = RAW_GAMES_DIR, output_dir: Path = PROCESSED_DIR) -> Path:
    """Concats every raw games file and applies the shared preprocessing steps
    (alias fixes, dedup, winner computation). Re-scraped-but-unchanged games are
    a no-op thanks to the existing dedupe key; only genuinely new rows survive."""
    preprocessor = Preprocessor()
    preprocessor.read_data_in_folder(str(raw_dir))
    preprocessed_df = preprocessor.preprocess_games_df()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "games_preprocessed.csv"
    preprocessed_df.to_csv(output_path, index=False)

    return output_path


def run_cinturao(preprocessed_path: Path, output_dir: Path = PROCESSED_DIR) -> Path:
    """Recomputes the full belt-succession history over the merged dataset."""
    cinturao = Cinturao(preprocessed_games_path=str(preprocessed_path))
    cinturao.read_games_data()
    cinturao_games = cinturao.run_cinturao_algorithm()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "games_cinturao.csv"
    cinturao_games.to_csv(output_path, index=False)

    return output_path


def regenerate_seed_csv(cinturao_output: Path, seed_path: Path = SEED_GAMES_PATH) -> None:
    """Overwrites backend/seed_data/games.csv with the freshly computed result."""
    cinturao_games = pd.read_csv(cinturao_output)
    cinturao_games.to_csv(seed_path, index=False)


def check_unresolved_teams(
    games_path: Path = SEED_GAMES_PATH,
    teams_path: Path = SEED_TEAMS_PATH,
    output_path: Path = UNRESOLVED_TEAMS_PATH,
) -> Path:
    """Diffs team names appearing in the new games.csv against the known team
    directory and writes any unresolved names for human review. Never raises —
    an unresolved name is a review item for the PR, not a pipeline failure."""
    games_df = pd.read_csv(games_path)
    teams_df = pd.read_csv(teams_path)

    known_team_names = set(teams_df["Nome"])
    game_team_names = set(games_df["Mandante"]) | set(games_df["Visitante"])
    unresolved_names = sorted(game_team_names - known_team_names)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(unresolved_names)
    output_path.write_text(f"{content}\n" if content else "")

    return output_path
