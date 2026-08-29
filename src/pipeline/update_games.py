import argparse
from datetime import datetime

from src.pipeline import tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape recent games and update the seeded games CSV.")
    parser.add_argument(
        "--since-year",
        type=int,
        default=datetime.now().year - 1,
        help="Only scrape tournaments whose URL year is >= this (default: last year, to cover a season still being finalized).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run merge/preprocess/cinturao over the already-scraped raw data without re-scraping or touching backend/seed_data/games.csv.",
    )
    args = parser.parse_args()

    if not args.dry_run:
        raw_path = tasks.scrape_recent_games(since_year=args.since_year)
        print(f"Scraped games written to {raw_path}")

    preprocessed_path = tasks.merge_and_preprocess()
    print(f"Merged/preprocessed games written to {preprocessed_path}")

    cinturao_path = tasks.run_cinturao(preprocessed_path)
    print(f"Cinturão history written to {cinturao_path}")

    if args.dry_run:
        print("Dry run: not overwriting backend/seed_data/games.csv")
        return

    tasks.regenerate_seed_csv(cinturao_path)
    print(f"Updated {tasks.SEED_GAMES_PATH}")

    unresolved_path = tasks.check_unresolved_teams()
    print(f"Unresolved team names (if any) written to {unresolved_path}")


if __name__ == "__main__":
    main()
